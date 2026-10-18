"""Four-point homography, warped coverage masks, and alpha compositing."""
import json

import cv2 as cv
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .common import ROOT, read_image, save_image, save_json


def poster(style, size):
    width, height = size
    colour, accent = ((19, 38, 57), (239, 181, 84)) if style == "studio" else ((20, 65, 50), (217, 239, 183))
    image = Image.new("RGB", (width, height), colour)
    draw = ImageDraw.Draw(image)
    # Pillow ships a scalable default font, avoiding platform-specific fonts.
    title, subtitle = (("OPEN STUDIO", "ART / DESIGN / IDEAS") if style == "studio"
                       else ("GROW TOGETHER", "COMMUNITY GARDEN / WEEKEND WORKSHOP"))
    def fitting_font(text, initial_size):
        size = int(initial_size)
        while size > 10:
            font = ImageFont.load_default(size=size)
            if draw.textbbox((0, 0), text, font=font)[2] <= width*.87:
                return font
            size -= 1
        return ImageFont.load_default(size=10)
    title_font = fitting_font(title, height*.35)
    sub_font = fitting_font(subtitle, height*.13)
    draw.rectangle((12, 12, width-13, height-13), outline=accent, width=max(2, height//80))
    draw.text((width*.06, height*.18), title, font=title_font, fill=accent)
    draw.text((width*.06, height*.64), subtitle, font=sub_font, fill=(245, 245, 235))
    return cv.cvtColor(np.array(image), cv.COLOR_RGB2BGR)


def composite(background, overlay, destination, alpha=.8):
    destination = np.asarray(destination, dtype=np.float32)
    if destination.shape != (4, 2) or not np.isfinite(destination).all():
        raise ValueError("Four finite TL/TR/BR/BL destination corners required")
    if not 0 <= alpha <= 1:
        raise ValueError("Alpha must lie between zero and one")
    contour = destination.reshape(-1, 1, 2)
    if not cv.isContourConvex(contour) or abs(cv.contourArea(contour)) < 16:
        raise ValueError("Destination must be a non-degenerate convex quadrilateral")
    height, width = overlay.shape[:2]
    source = np.float32([[0, 0], [width-1, 0], [width-1, height-1], [0, height-1]])
    H = cv.getPerspectiveTransform(source, destination)
    size = (background.shape[1], background.shape[0])
    # Warp premultiplied colours and coverage with identical interpolation.
    # Black is valid content, so coverage never depends on pixel brightness.
    warped = cv.warpPerspective(overlay.astype(np.float32), H, size, flags=cv.INTER_LINEAR)
    coverage = cv.warpPerspective(np.ones((height, width), dtype=np.float32), H, size,
                                   flags=cv.INTER_LINEAR)
    result = background.astype(np.float32)*(1-alpha*coverage[:, :, None]) + alpha*warped
    return np.clip(np.rint(result), 0, 255).astype(np.uint8), H, coverage


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    pairs = json.loads((ROOT / "assets/q3/pairs.json").read_text())
    fig, axes = plt.subplots(len(pairs), 3, figsize=(12, 6.3), layout="constrained")
    results = []
    for row, pair in enumerate(pairs):
        background = read_image(ROOT / pair["background"])
        overlay = poster(pair["poster_style"], pair["poster_size"])
        result, H, coverage = composite(background, overlay, pair["corners"], pair["alpha"])
        folder = output / pair["name"]
        save_image(folder / "poster.png", overlay)
        save_image(folder / "composite.jpg", result)
        save_image(folder / "coverage.png", np.rint(coverage*255).astype(np.uint8))
        selected = background.copy()
        cv.polylines(selected, [np.int32(pair["corners"])], True, (0, 190, 255), 3, cv.LINE_AA)
        for i, (x, y) in enumerate(pair["corners"], 1):
            cv.circle(selected, (x, y), 7, (0, 0, 255), -1)
            cv.putText(selected, str(i), (x+10, y-10), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv.LINE_AA)
        for col, image in enumerate([selected, overlay, result]):
            axes[row, col].imshow(cv.cvtColor(image, cv.COLOR_BGR2RGB))
            axes[row, col].axis("off")
        axes[row, 0].set_title(pair["name"].replace("_", " "), fontsize=10)
        axes[row, 1].set_title("Original overlay graphic", fontsize=10)
        axes[row, 2].set_title(f"Composite (alpha {pair['alpha']})", fontsize=10)
        mapped = cv.perspectiveTransform(np.float32([[[0, 0], [overlay.shape[1]-1, 0],
                         [overlay.shape[1]-1, overlay.shape[0]-1], [0, overlay.shape[0]-1]]]), H)[0]
        metrics = dict(**pair, homography_overlay_to_background=H,
            maximum_corner_error_px=float(np.linalg.norm(mapped-np.asarray(pair["corners"]), axis=1).max()))
        save_json(folder / "parameters.json", metrics); results.append(metrics)
    fig.savefig(output / "overview.png", dpi=180); plt.close(fig)
    save_json(output / "results.json", results)
    return results
