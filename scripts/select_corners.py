"""Select Q3 destination corners with four mouse clicks: TL, TR, BR, BL."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cv2 as cv
import matplotlib.pyplot as plt
from assignment2.common import ROOT, read_image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pair", type=int, choices=[0, 1], required=True)
    args = parser.parse_args()
    path = ROOT / "assets/q3/pairs.json"
    pairs = json.loads(path.read_text())
    pair = pairs[args.pair]
    image = read_image(ROOT / pair["background"])
    plt.figure(figsize=(14, 9)); plt.imshow(cv.cvtColor(image, cv.COLOR_BGR2RGB))
    plt.title("Click TL, TR, BR, BL; close to cancel")
    selected = plt.ginput(4, timeout=0); plt.close()
    if len(selected) != 4:
        raise SystemExit("Cancelled; coordinates unchanged")
    from assignment2.compositing import composite, poster
    points = [[round(x), round(y)] for x, y in selected]
    composite(image, poster(pair["poster_style"], pair["poster_size"]), points, pair["alpha"])
    pair["corners"] = points
    pair["selection"] = "Four mouse clicks using scripts/select_corners.py; TL/TR/BR/BL."
    path.write_text(json.dumps(pairs, indent=2)+"\n")
    print(f"Saved corners for {pair['name']}; rerun Q3 and the report.")


if __name__ == "__main__":
    main()
