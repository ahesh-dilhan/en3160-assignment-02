"""Prepare original-colour figures with black labels and measured LaTeX tables."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "tmp/matplotlib"))
os.environ.setdefault("MPLBACKEND", "Agg")

import cv2 as cv
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from assignment2.common import read_image
from assignment2.ransac import generate_points
from assignment2.registration import register

FIG = ROOT / "report/figures"
plt.rcParams.update({"font.family": "serif", "font.size": 9, "text.color": "black",
    "axes.labelcolor": "black", "axes.edgecolor": "black", "xtick.color": "black",
    "ytick.color": "black", "figure.facecolor": "white", "savefig.facecolor": "white"})


def load(task):
    return json.loads((ROOT / f"outputs/{task}/results.json").read_text())


def logo():
    source = Image.open(ROOT / "assets/report/uom_logo_original.png").convert("RGBA")
    white = Image.new("RGBA", source.size, "white")
    white.alpha_composite(source)
    white.convert("RGB").save(FIG / "uom_logo.png")


def sunflower(q1):
    image = read_image(ROOT / "images/the_berry_farms_sunflower_field.jpeg", cv.IMREAD_REDUCED_COLOR_4)
    detections = []
    import csv
    with (ROOT / "outputs/q1/detections.csv").open() as stream:
        detections = [{k: float(v) for k, v in row.items()} for row in csv.DictReader(stream)]
    marked = image.copy()
    for blob in detections:
        centre = (round(blob["x"]), round(blob["y"]))
        radius = round(blob["radius"])
        cv.circle(marked, centre, radius, (255, 220, 0), 1, cv.LINE_AA)
    for rank, blob in enumerate(q1["largest"], 1):
        point = (min(343, round(blob["x"]+blob["radius"]+2)), round(blob["y"])-3)
        cv.circle(marked, (round(blob['x']), round(blob['y'])), round(blob['radius']), (0, 0, 255), 1, cv.LINE_AA)
        cv.putText(marked, str(rank), point, cv.FONT_HERSHEY_SIMPLEX, .4, (255, 255, 255), 3, cv.LINE_AA)
        cv.putText(marked, str(rank), point, cv.FONT_HERSHEY_SIMPLEX, .4, (0, 0, 0), 1, cv.LINE_AA)
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.85), layout="constrained")
    for ax, data, title in zip(axes, [image, marked], ["(a) Reduced input: 360 x 360", "(b) LoG detections; largest five numbered"]):
        ax.imshow(cv.cvtColor(data, cv.COLOR_BGR2RGB)); ax.set_title(title, fontsize=9, color="black"); ax.axis("off")
    fig.savefig(FIG / "sunflowers.png", dpi=240); plt.close(fig)


def ransac(q2):
    points = generate_points(q2["data_seed"])
    fits = q2["sequences"]["line_first"]
    fig, ax = plt.subplots(figsize=(7, 3.8), layout="constrained")
    ax.scatter(*points.T, s=13, facecolors="white", edgecolors="#687888", linewidths=.5, label="All points")
    x = np.array([-15, 17])
    ax.plot(x, -x+2, color="#687888", linestyle=(0, (7, 3)), lw=.7, label="True line")
    ax.add_patch(plt.Circle((2, 3), 10, fill=False, color="#687888", linestyle=(0, (7, 3)), lw=.7, label="True circle"))
    for kind in ["line", "circle"]:
        fit = fits[kind]
        colour = "#cb563b" if kind == "line" else "#007f86"
        data = points[fit["inlier_indices"]]
        if kind == "line":
            ax.scatter(*data.T, marker="+", color=colour, s=22, lw=.8, label="Line inliers")
        else:
            ax.scatter(*data.T, marker="o", facecolors="white", edgecolors=colour, s=19, lw=.8, label="Circle inliers")
        sample = points[fit["sample_indices"]]
        ax.scatter(*sample.T, marker="s" if kind == "line" else "^", facecolors=colour, edgecolors=colour,
                   s=38, label=f"Winning {kind} sample", zorder=5)
        for model, style, label, lw in [(fit["sample_parameters"], ":" if kind=="line" else "-.", f"Sample {kind}", .9),
                                       (fit["parameters"], "-" if kind=="line" else "--", f"Refined {kind}", 1.2)]:
            if kind == "line":
                ax.plot(x, (model[2]-model[0]*x)/model[1], color=colour, linestyle=style, lw=lw, label=label)
            else:
                ax.add_patch(plt.Circle(model[:2], model[2], fill=False, color=colour, linestyle=style, lw=lw, label=label))
    ax.set(xlim=(-15, 17), ylim=(-14, 17), xlabel="$x$", ylabel="$y$")
    ax.set_aspect("equal")
    ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.01, 1), edgecolor="black", framealpha=1)
    fig.savefig(FIG / "ransac.png", dpi=240); plt.close(fig)


def composites(q3):
    fig, axes = plt.subplots(2, 2, figsize=(7, 4.7), layout="constrained")
    for row, pair in enumerate(q3):
        for col, path in enumerate([ROOT / pair["background"], ROOT / f"outputs/q3/{pair['name']}/composite.jpg"]):
            image = read_image(path)
            axes[row, col].imshow(cv.cvtColor(image, cv.COLOR_BGR2RGB))
            axes[row, col].axis("off")
            title = "Modern facade" if row == 0 else "Garage door"
            axes[row, col].set_title(f"{title}: {'input' if col == 0 else 'composite'}", fontsize=9)
    fig.savefig(FIG / "composites.png", dpi=240); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(7, 2.55), layout="constrained")
    for ax, pair in zip(axes, q3):
        path = ROOT / f"outputs/q3/{pair['name']}/composite.jpg"
        ax.imshow(cv.cvtColor(read_image(path), cv.COLOR_BGR2RGB))
        ax.axis("off")
        ax.set_title("Modern facade" if pair['poster_style'] == 'studio' else "Garage door", color="black", fontsize=9)
    fig.savefig(FIG / "composites_compact.png", dpi=260); plt.close(fig)


def pcb(q4):
    fig, axes = plt.subplots(1, 5, figsize=(7, 2.05), layout="constrained")
    cmap = plt.get_cmap("magma").copy(); cmap.set_bad("white")
    for ax, row in zip(axes, q4):
        folder = ROOT / "outputs/q4" / row["image"]
        difference = read_image(folder / "difference.png").mean(axis=2)
        valid = read_image(folder / "valid_mask.png", cv.IMREAD_GRAYSCALE) > 0
        ax.imshow(np.ma.array(difference, mask=~valid), cmap=cmap, vmin=0, vmax=100)
        ax.set_title(row["image"], fontsize=10); ax.axis("off")
    fig.savefig(FIG / "pcb_differences.png", dpi=240); plt.close(fig)
    result = register(read_image(ROOT / "images/pcbs/ADAD1.jpg"),
                      read_image(ROOT / "images/pcbs/AECC1.jpg"), match_colour=(60, 220, 100))
    # Recompute only the drawing colour; keep the recorded numerical metrics.
    Image.fromarray(cv.cvtColor(result["matches"], cv.COLOR_BGR2RGB)).save(FIG / "pcb_matches.png")


def tables(q1, q2, q3, q4):
    lines = ["% Generated from measured experiment outputs; do not edit by hand.",
             rf"\newcommand{{\BlobCount}}{{{q1['detected_count']}}}",
             "\\newcommand{\\BlobRows}{%"]
    for i, row in enumerate(q1["largest"], 1):
        lines.append(f"{i} & {row['x']:.0f} & {row['y']:.0f} & {row['sigma']:.3f} & {row['radius']:.3f} & {row['response']:.3f} " + r"\\")
    lines.append("}")
    lines.append(r"\newcommand{\FitRows}{%")
    line = q2["sequences"]["line_first"]["line"]
    circle = q2["sequences"]["line_first"]["circle"]
    a, b, d = line["parameters"]; x, y, r = circle["parameters"]
    lines.append(rf"Line & $a={a:.4f},\ b={b:.4f},\ d={d:.4f}$ & {line['inlier_count']} & {line['inlier_rmse']:.4f} " + r"\\")
    lines.append(rf"Circle & $c_x={x:.4f},\ c_y={y:.4f},\ r={r:.4f}$ & {circle['inlier_count']} & {circle['inlier_rmse']:.4f} " + r"\\")
    lines.append("}")
    lines.append(r"\newcommand{\PcbRows}{%")
    for row in q4:
        lines.append(f"{row['image']} & {row['ratio_matches']} & {row['ransac_inliers']} & {row['median_reprojection_error_small_px']:.3f} & {100*row['valid_overlap_fraction']:.1f}\\% & {row['raw_overlap_mae']:.2f} " + r"\\")
    lines.append("}")
    lines.append(r"\newcommand{\CornerRows}{%")
    for pair in q3:
        name = "Studio" if pair["poster_style"] == "studio" else "Garden"
        corners = ", ".join(f"({x},{y})" for x, y in pair["corners"])
        lines.append(f"{name} & {corners} & {pair['alpha']} " + r"\\")
    lines.append("}")
    (ROOT / "report/data.tex").write_text("\n".join(lines)+"\n", encoding="utf-8")


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    q1, q2, q3, q4 = [load(task) for task in ["q1", "q2", "q3", "q4"]]
    logo(); sunflower(q1); ransac(q2); composites(q3); pcb(q4); tables(q1, q2, q3, q4)
    print(f"Prepared original-colour figures with black labels in {ROOT / 'report'}")


if __name__ == "__main__":
    main()
