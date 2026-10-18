"""SIFT/BFMatcher registration with RANSAC and valid-overlap differences."""
import csv

import cv2 as cv
import matplotlib.pyplot as plt
import numpy as np

from .common import ROOT, read_image, resize_for_features, save_image, save_json


def estimate_homography(source_points, destination_points, threshold=3.0):
    source = np.asarray(source_points, dtype=np.float32).reshape(-1, 1, 2)
    destination = np.asarray(destination_points, dtype=np.float32).reshape(-1, 1, 2)
    if len(source) != len(destination) or len(source) < 4:
        raise ValueError("At least four paired matches required")
    cv.setRNGSeed(230145)
    H, mask = cv.findHomography(source, destination, cv.RANSAC, threshold,
                                maxIters=10000, confidence=0.999)
    if H is None or mask is None or not np.isfinite(H).all() or abs(H[2, 2]) < 1e-12:
        raise RuntimeError("Homography estimation failed")
    H = H/H[2, 2]
    if np.linalg.matrix_rank(H) < 3 or mask.sum() < 8:
        raise RuntimeError("Insufficient geometric support for the homography")
    predicted = cv.perspectiveTransform(source, H).reshape(-1, 2)
    errors = np.linalg.norm(predicted-destination.reshape(-1, 2), axis=1)
    return H, mask.ravel().astype(bool), errors


def warp_and_difference(source, template, H):
    height, width = template.shape[:2]
    aligned = cv.warpPerspective(source, H, (width, height), flags=cv.INTER_LINEAR)
    # Linear interpolation of an all-one mask detects partly padded pixels too.
    mask = cv.warpPerspective(np.ones(source.shape[:2], dtype=np.float32), H,
                              (width, height), flags=cv.INTER_LINEAR) > .999
    mask = cv.erode(mask.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    if not mask.any():
        raise RuntimeError("Images have no valid overlap")
    difference = cv.absdiff(aligned, template)
    difference[~mask] = 0
    return aligned, difference, mask


def register(source, template, template_features=None, max_side=1600,
             ratio=0.72, reprojection_threshold=3.0, match_colour=(60, 220, 100)):
    small_source, source_scale = resize_for_features(source, max_side)
    small_template, template_scale = resize_for_features(template, max_side)
    sift = cv.SIFT_create(nfeatures=8000)
    source_keypoints, source_descriptors = sift.detectAndCompute(cv.cvtColor(small_source, cv.COLOR_BGR2GRAY), None)
    if template_features is None:
        template_features = sift.detectAndCompute(cv.cvtColor(small_template, cv.COLOR_BGR2GRAY), None)
    template_keypoints, template_descriptors = template_features
    if source_descriptors is None or template_descriptors is None:
        raise RuntimeError("No SIFT descriptors found")
    matcher = cv.BFMatcher(cv.NORM_L2)
    neighbours = matcher.knnMatch(source_descriptors, template_descriptors, k=2)
    good = [pair[0] for pair in neighbours if len(pair) == 2 and pair[0].distance < ratio*pair[1].distance]
    if len(good) < 8:
        raise RuntimeError(f"Only {len(good)} ratio-filtered matches")
    source_points = np.float32([source_keypoints[m.queryIdx].pt for m in good])
    template_points = np.float32([template_keypoints[m.trainIdx].pt for m in good])
    H_small, inliers, errors = estimate_homography(source_points, template_points, reprojection_threshold)
    # H_small maps scaled source -> scaled template; undo both image scales.
    H = np.linalg.inv(template_scale) @ H_small @ source_scale
    H /= H[2, 2]
    aligned, difference, valid = warp_and_difference(source, template, H)
    matches = cv.drawMatches(small_source, source_keypoints, small_template, template_keypoints,
        good, None, matchesMask=inliers.astype(int).tolist(),
        matchColor=match_colour, flags=cv.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
    inlier_hull = cv.convexHull(template_points[inliers])
    coverage = cv.contourArea(inlier_hull)/(small_template.shape[0]*small_template.shape[1])
    metrics = dict(source_keypoints=len(source_keypoints), template_keypoints=len(template_keypoints),
        ratio_threshold=ratio, ratio_matches=len(good), ransac_inliers=int(inliers.sum()),
        inlier_ratio=float(inliers.mean()), median_reprojection_error_small_px=float(np.median(errors[inliers])),
        reprojection_threshold_small_px=reprojection_threshold, feature_max_side=max_side,
        inlier_hull_fraction_of_template=float(coverage), homography_source_to_template=H,
        valid_overlap_fraction=float(valid.mean()), raw_overlap_mae=float(difference[valid].mean()),
        difference_units="8-bit intensity, absolute per-channel difference")
    return dict(aligned=aligned, difference=difference, valid=valid, matches=matches, metrics=metrics)


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    template = read_image(ROOT / "images/pcbs/AECC1.jpg")
    small_template, _ = resize_for_features(template)
    sift = cv.SIFT_create(nfeatures=8000)
    features = sift.detectAndCompute(cv.cvtColor(small_template, cv.COLOR_BGR2GRAY), None)
    results = []
    panels = []
    for name in ["AAAA1", "ADAD1", "AECC2", "AECC3", "AECC4"]:
        print(f"  Registering {name} against AECC1...", flush=True)
        source = read_image(ROOT / f"images/pcbs/{name}.jpg")
        result = register(source, template, features)
        folder = output / name
        save_image(folder / "aligned.jpg", result["aligned"])
        save_image(folder / "difference.png", result["difference"])
        save_image(folder / "valid_mask.png", result["valid"].astype(np.uint8)*255)
        save_image(folder / "matches.jpg", result["matches"])
        overlay = cv.addWeighted(result["aligned"], .5, template, .5, 0)
        overlay[~result["valid"]] = 0
        save_image(folder / "overlay.jpg", overlay)
        metrics = dict(image=name, **result["metrics"])
        save_json(folder / "metrics.json", metrics)
        results.append(metrics)
        panels.append((name, source, result["aligned"], result["difference"], result["valid"]))
    fig, axes = plt.subplots(5, 4, figsize=(11, 14), layout="constrained")
    for row, (name, source, aligned, difference, valid) in enumerate(panels):
        for col, image in enumerate([source, aligned, template, difference]):
            display = cv.cvtColor(image, cv.COLOR_BGR2RGB)
            if col == 3:
                # Mean-channel intensity, fixed range: no per-image rescaling.
                display = np.ma.array(image.mean(axis=2), mask=~valid)
                cmap = plt.get_cmap("magma").copy(); cmap.set_bad("#d4d4d4")
                axes[row, col].imshow(display, cmap=cmap, vmin=0, vmax=100)
            else:
                axes[row, col].imshow(display)
            axes[row, col].axis("off")
        axes[row, 0].set_title(name)
    for ax, title in zip(axes[0], ["AAAA1: input", "Aligned", "AECC1 template", "Raw difference [0,100]"]):
        ax.set_title(title, fontsize=10)
    fig.savefig(output / "overview.png", dpi=170); plt.close(fig)
    save_json(output / "results.json", results)
    columns = ["image", "ratio_matches", "ransac_inliers", "inlier_ratio",
               "median_reprojection_error_small_px", "valid_overlap_fraction", "raw_overlap_mae"]
    with (output / "metrics.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader(); writer.writerows(results)
    return results
