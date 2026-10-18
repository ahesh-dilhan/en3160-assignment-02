"""Scale-normalized LoG, three-dimensional extrema, and overlap suppression."""
from dataclasses import asdict, dataclass
import csv

import cv2 as cv
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import gaussian_filter, gaussian_laplace, maximum_filter

from .common import ROOT, read_image, save_image, save_json


@dataclass
class Blob:
    x: float
    y: float
    sigma: float
    radius: float
    response: float


def circle_overlap(first, second):
    """Intersection area divided by the area of the smaller disk."""
    r, s = first.radius, second.radius
    d = np.hypot(first.x - second.x, first.y - second.y)
    if d >= r + s:
        return 0.0
    if d <= abs(r - s):
        return 1.0
    area = (r*r*np.arccos(np.clip((d*d+r*r-s*s)/(2*d*r), -1, 1))
            + s*s*np.arccos(np.clip((d*d+s*s-r*r)/(2*d*s), -1, 1))
            - 0.5*np.sqrt(max(0, (-d+r+s)*(d+r-s)*(d-r+s)*(d+r+s))))
    return float(area / (np.pi * min(r, s)**2))


def detect_blobs(scalar_image, sigmas, threshold=0.025, overlap=0.35,
                 support_mask=None, minimum_support=0.5):
    image = np.asarray(scalar_image, dtype=np.float64)
    sigmas = np.asarray(sigmas, dtype=float)
    if image.ndim != 2 or len(sigmas) < 3 or np.any(sigmas <= 0) or np.any(np.diff(sigmas) <= 0):
        raise ValueError("Need a 2D image and at least three increasing positive sigmas")
    responses = np.stack([-s*s*gaussian_laplace(image, s, mode="reflect") for s in sigmas])
    extrema = (responses == maximum_filter(responses, size=(3, 3, 3), mode="constant"))
    extrema &= responses >= threshold
    # End-scale maxima are censored: they have no neighbour on both sides.
    extrema[[0, -1]] = False
    candidates = []
    hessians = {}
    for k, y, x in np.argwhere(extrema):
        radius = np.sqrt(2) * sigmas[k]
        if min(x, y, image.shape[1]-1-x, image.shape[0]-1-y) < radius:
            continue
        if support_mask is not None:
            # A yellow annulus around a dark blob is evidence for a sunflower
            # centre; the dark centre itself need not contain yellow pixels.
            r = int(np.ceil(2.2*radius))
            y0, y1 = max(0, y-r), min(image.shape[0], y+r+1)
            x0, x1 = max(0, x-r), min(image.shape[1], x+r+1)
            yy, xx = np.mgrid[y0-y:y1-y, x0-x:x1-x]
            disk = (xx*xx + yy*yy >= radius*radius) & (xx*xx + yy*yy <= (2.2*radius)**2)
            patch = support_mask[y0:y1, x0:x1]
            if not disk.any() or patch[disk].mean() < minimum_support:
                continue
            # Yellow must surround the centre rather than sit on only one side.
            sectors = ((np.arctan2(yy, xx)+np.pi)*8/(2*np.pi)).astype(int) % 8
            observed = [disk & (sectors == j) for j in range(8)]
            supported = [patch[sector].mean() >= .3 for sector in observed if sector.any()]
            if np.mean(supported) < .75:
                continue
            # Reject strongly elongated dark gaps, using curvature symmetry.
            if k not in hessians:
                hessians[k] = [gaussian_filter(image, sigmas[k], order=order)
                               for order in [(0, 2), (1, 1), (2, 0)]]
            hxx, hxy, hyy = [h[y, x] for h in hessians[k]]
            eigenvalues = np.linalg.eigvalsh([[hxx, hxy], [hxy, hyy]])
            if eigenvalues[1] >= 0 or eigenvalues[1]/eigenvalues[0] < .5:
                continue
        candidates.append(Blob(float(x), float(y), float(sigmas[k]), float(radius),
                               float(responses[k, y, x])))
    selected = []
    for blob in sorted(candidates, key=lambda b: b.response, reverse=True):
        if all(circle_overlap(blob, other) <= overlap for other in selected):
            selected.append(blob)
    return selected, responses


def run(output, sigma_min=1.5, sigma_max=16.0, scales=36, threshold=0.12):
    output.mkdir(parents=True, exist_ok=True)
    image = read_image(ROOT / "images/the_berry_farms_sunflower_field.jpeg",
                       cv.IMREAD_REDUCED_COLOR_4)
    # Dark flower disks are more blob-like than their ring of bright petals.
    darkness = 1-cv.cvtColor(image, cv.COLOR_BGR2GRAY).astype(float)/255
    hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    support = ((hsv[:, :, 0] >= 15) & (hsv[:, :, 0] <= 40)
               & (hsv[:, :, 1] >= 100) & (hsv[:, :, 2] >= 110))
    sigmas = np.geomspace(sigma_min, sigma_max, scales)
    blobs, responses = detect_blobs(darkness, sigmas, threshold, support_mask=support)
    largest = sorted(blobs, key=lambda b: b.radius, reverse=True)[:5]
    annotated = image.copy()
    for blob in blobs:
        cv.circle(annotated, (round(blob.x), round(blob.y)), round(blob.radius), (255, 220, 0), 1, cv.LINE_AA)
    for i, blob in enumerate(largest, 1):
        cv.circle(annotated, (round(blob.x), round(blob.y)), round(blob.radius), (0, 0, 255), 1, cv.LINE_AA)
        cv.putText(annotated, str(i), (round(blob.x+blob.radius), round(blob.y)),
                   cv.FONT_HERSHEY_SIMPLEX, .35, (0, 0, 255), 1, cv.LINE_AA)
    save_image(output / "detections.png", annotated)
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), layout="constrained")
    axes[0].imshow(cv.cvtColor(image, cv.COLOR_BGR2RGB)); axes[0].set_title("Input: 360 x 360")
    axes[1].imshow(darkness, cmap="gray", vmin=0, vmax=1); axes[1].set_title("Darkness signal for LoG")
    axes[2].imshow(cv.cvtColor(annotated, cv.COLOR_BGR2RGB)); axes[2].set_title(f"{len(blobs)} blobs; largest five in red")
    for ax in axes: ax.axis("off")
    fig.savefig(output / "overview.png", dpi=180); plt.close(fig)
    parameters = dict(sigma_min=sigma_min, sigma_max=sigma_max, scales=scales,
                      scale_spacing="geometric", threshold=threshold, overlap=0.35,
                      minimum_yellow_annulus_support=0.5, annulus_radius_factors=[1, 2.2],
                      angular_support="at least 75% of observed 8 sectors have >=30% yellow",
                      minimum_hessian_curvature_ratio=0.5,
                      scalar_signal="1-grayscale/255", detection_target="dark sunflower centres",
                      radius_rule="sqrt(2)*sigma", coordinate_system="reduced image pixels",
                      image_shape=image.shape, sigmas=sigmas, detected_count=len(blobs),
                      largest=[asdict(b) for b in largest])
    save_json(output / "results.json", parameters)
    with (output / "detections.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(Blob.__dataclass_fields__))
        writer.writeheader(); writer.writerows(asdict(b) for b in blobs)
    return parameters
