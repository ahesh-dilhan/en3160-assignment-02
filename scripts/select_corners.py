"""Click Q3 corners TL, TR, BR, BL. Enter saves, R resets, Esc cancels."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / "tmp/matplotlib"))
import cv2 as cv
import numpy as np

from assignment2.common import ROOT, read_image
from assignment2.compositing import composite, poster

# Stable surface guides, independent of any previously saved selection.
SURFACE_GUIDES = {
    "modern_open_studio": [[215, 405], [953, 508], [953, 556], [215, 461]],
    "garage_community_garden": [[454, 683], [782, 683], [786, 800], [450, 800]],
}


def select(pair, index):
    image_path = ROOT / pair["background"]
    image = read_image(image_path)
    surface = np.array(SURFACE_GUIDES[pair["name"]], dtype=np.float32)
    x0, y0 = np.maximum(0, np.floor(surface.min(axis=0)-80)).astype(int)
    x1, y1 = np.minimum([image.shape[1], image.shape[0]], np.ceil(surface.max(axis=0)+80)).astype(int)
    crop = image[y0:y1, x0:x1]
    scale = min(1100/crop.shape[1], 720/crop.shape[0], 1.5)
    width, height = round(crop.shape[1]*scale), round(crop.shape[0]*scale)
    shown = cv.resize(crop, (width, height), interpolation=cv.INTER_LINEAR)
    sx, sy = width/crop.shape[1], height/crop.shape[0]
    header_height = 90
    points, events = [], []
    title = f"EN3160 Q3 - pair {index}: {pair['name']}"

    def on_mouse(event, x, y, flags, userdata):
        if event != cv.EVENT_LBUTTONDOWN or len(points) == 4:
            return
        if not (0 <= x < width and header_height <= y < header_height+height):
            return
        point = [round(x/sx)+int(x0), round((y-header_height)/sy)+int(y0)]
        points.append(point)
        events.append(dict(point=point, display_xy=[x, y-header_height],
                           utc=datetime.now(timezone.utc).isoformat()))

    cv.namedWindow(title, cv.WINDOW_AUTOSIZE)
    cv.setMouseCallback(title, on_mouse)
    message = ""
    try:
        while True:
            display = np.full((height+header_height, width, 3), 255, dtype=np.uint8)
            display[header_height:] = shown
            guide = np.rint((surface-[x0, y0])*[sx, sy]).astype(np.int32)
            guide[:, 1] += header_height
            cv.polylines(display, [guide], True, (0, 180, 255), 2, cv.LINE_AA)
            for rank, (gx, gy) in enumerate(guide, 1):
                cv.circle(display, (int(gx), int(gy)), 8, (0, 180, 255), 2, cv.LINE_AA)
                cv.putText(display, str(rank), (int(gx)+11, int(gy)-9), cv.FONT_HERSHEY_SIMPLEX,
                           .7, (255, 255, 255), 3, cv.LINE_AA)
                cv.putText(display, str(rank), (int(gx)+11, int(gy)-9), cv.FONT_HERSHEY_SIMPLEX,
                           .7, (0, 0, 0), 1, cv.LINE_AA)
            for rank, (x, y) in enumerate(points, 1):
                xy = (round((x-x0)*sx), round((y-y0)*sy)+header_height)
                cv.circle(display, xy, 5, (0, 0, 255), -1, cv.LINE_AA)
                cv.putText(display, str(rank), (xy[0]+8, xy[1]-7), cv.FONT_HERSHEY_SIMPLEX,
                           .6, (255, 255, 255), 3, cv.LINE_AA)
                cv.putText(display, str(rank), (xy[0]+8, xy[1]-7), cv.FONT_HERSHEY_SIMPLEX,
                           .6, (0, 0, 0), 1, cv.LINE_AA)
            instructions = ["Click the FOUR ORANGE CORNERS, not the photo/window edges.",
                f"{len(points)}/4 selected | Enter: save | R: reset | Backspace: undo | Esc: cancel",
                message or "Order: 1 top-left, 2 top-right, 3 bottom-right, 4 bottom-left."]
            for line, text in enumerate(instructions):
                cv.putText(display, text, (12, 22+line*27), cv.FONT_HERSHEY_SIMPLEX,
                           .52, (0, 0, 0), 1, cv.LINE_AA)
            cv.imshow(title, display)
            key = cv.waitKey(30) & 0xff
            if key == 27 or cv.getWindowProperty(title, cv.WND_PROP_VISIBLE) < 1:
                return None
            if key in (ord('r'), ord('R')):
                points.clear(); events.clear(); message = ""
            elif key in (8, 127) and points:
                points.pop(); events.pop(); message = ""
            elif key in (10, 13):
                if len(points) != 4:
                    message = "Select all four corners before saving."
                    continue
                area = abs(cv.contourArea(np.asarray(points, dtype=np.float32)))
                if area > 3*abs(cv.contourArea(surface)):
                    message = "Selection too large. Press R, then click ONLY the orange corners."
                    continue
                try:
                    composite(image, poster(pair["poster_style"], pair["poster_size"]),
                              points, pair["alpha"])
                except ValueError as error:
                    message = str(error)
                    continue
                return dict(corners=points, click_events=events,
                    image_sha256=hashlib.sha256(image_path.read_bytes()).hexdigest(),
                    display_size=[width, height], original_size=[image.shape[1], image.shape[0]],
                    view_roi=[int(x0), int(y0), int(x1), int(y1)])
    finally:
        cv.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--pair", type=int, choices=[0, 1])
    choice.add_argument("--all", action="store_true", help="Select both pairs in sequence")
    args = parser.parse_args()
    path = ROOT / "assets/q3/pairs.json"
    evidence_path = ROOT / "assets/q3/corner_clicks.json"
    pairs = json.loads(path.read_text())
    evidence = json.loads(evidence_path.read_text()) if evidence_path.exists() else {}
    for index in ([0, 1] if args.all else [args.pair]):
        pair = pairs[index]
        result = select(pair, index)
        if result is None:
            print(f"Cancelled {pair['name']}; its coordinates are unchanged.")
            return
        pair["corners"] = result["corners"]
        pair["selection"] = "Four mouse clicks using scripts/select_corners.py (OpenCV window); TL/TR/BR/BL."
        evidence[pair["name"]] = result
        path.write_text(json.dumps(pairs, indent=2)+"\n")
        evidence_path.write_text(json.dumps(evidence, indent=2)+"\n")
        print(f"Saved {pair['name']}: {pair['corners']}", flush=True)
    print("Corner selection saved. Rerun Q3 and rebuild the report.")


if __name__ == "__main__":
    main()
