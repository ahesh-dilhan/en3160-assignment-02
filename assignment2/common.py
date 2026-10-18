import json
from pathlib import Path

import cv2 as cv
import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def read_image(path, flags=cv.IMREAD_COLOR):
    image = cv.imread(str(path), flags)
    if image is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    return image


def save_image(path, image):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv.imwrite(str(path), image):
        raise OSError(f"Could not write image: {path}")


def save_json(path, data):
    def convert(value):
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, np.generic):
            return value.item()
        raise TypeError(type(value).__name__)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=convert, allow_nan=False) + "\n")


def resize_for_features(image, max_side=1600):
    height, width = image.shape[:2]
    factor = min(1.0, max_side / max(height, width))
    resized = cv.resize(image, (round(width * factor), round(height * factor)),
                        interpolation=cv.INTER_AREA) if factor < 1 else image.copy()
    # Exact x/y scales account for rounding of resized image dimensions.
    scale = np.diag([resized.shape[1] / width, resized.shape[0] / height, 1.0])
    return resized, scale
