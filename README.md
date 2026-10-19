# EN3160 Assignment 02: Fitting and Alignment

**Dilhan W.A. | 230145E**

Public repository: https://github.com/ahesh-dilhan/en3160-assignment-02

This project covers scale-space blob detection, custom RANSAC model fitting,
planar image compositing, and SIFT-based PCB registration.

## Current progress

- Reviewed the complete three-page assignment, including the example figures.
- Extracted and visually inspected all nine source images.
- Recorded requirements, data properties, and the implementation plan in
  [the assignment review](docs/assignment_review.md).
- Implemented and executed all four experiment pipelines.
- Validated the geometry with ten automated tests.
- Generated parameters, figures, matches, differences, and fitting-order comparisons.
- Published the repository. The report is authored in LaTeX with a separate
  university cover matching the supplied sample, black typography/rules, and original-colour figures.

## Local data preparation

Keep the original `a2images.zip` beside this README and run from PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/prepare_data.ps1
```

The script validates the archive checksum and expected files before extracting
to `images/`. The repository includes the original archive, assignment PDF, and
all nine extracted images, so a fresh clone already has the inputs ready to run.
The script can verify them or recreate missing extracted images without
overwriting modified files.

## Run the experiments

Python 3.12 was used. On this Windows workspace, a project-local runtime is ready:

```powershell
.\.runtime\python\python.exe scripts/run_assignment.py --task all
.\.runtime\python\python.exe -m pytest -q tests
```

On another computer, install Python 3.12, create a virtual environment, and install
the dependencies. The local runtime and caches are excluded from Git; all
assignment inputs and saved experiment results are included:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/run_assignment.py --task all
```

Use `--task q1`, `q2`, `q3`, or `q4` to run one experiment. Outputs are written
under `outputs/q1` through `outputs/q4`; numerical measurements are JSON/CSV.
The Q2 experiment includes seeds 0-19 for the fitting-order comparison.

## Repository contents

| Path | Contents |
| --- | --- |
| `en3160_assignment_02.pdf`, `a2images.zip` | Original supplied assignment and image archive |
| `images/` | All nine extracted input images |
| `assignment2/`, `scripts/`, `tests/` | Implementations, experiment/report commands, and geometry tests |
| `outputs/q1/` | Sunflower detections, CSV parameters, overview, and JSON results |
| `outputs/q2/` | Generated points, both fitting orders, and the 20-seed comparison |
| `outputs/q3/` | Both composites, overlay graphics, coverage masks, and homographies |
| `outputs/q4/` | All five aligned PCBs, feature matches, raw differences, masks, overlays, and metrics |
| `report/` | LaTeX source, measured tables, and report figures |
| `output/pdf/`, `output/latex/` | Latest PDF report and portable LaTeX source ZIP |
| `assets/`, `docs/` | Chosen image inputs, university logo, attributions, and assignment review |

Python/TeX installations, credentials, environment files, caches, editor state,
and temporary review images are excluded. Input provenance is recorded in
[images/README.md](images/README.md), and saved result conventions in
[outputs/README.md](outputs/README.md).

Q3 image attribution is in [assets/q3/ATTRIBUTION.md](assets/q3/ATTRIBUTION.md).
To select your own four destination corners interactively, run:

```powershell
python scripts/select_corners.py --pair 0
python scripts/select_corners.py --pair 1
```

Click top-left, top-right, bottom-right, bottom-left, then rerun Q3.

## LaTeX report

Source and build instructions: [report/README.md](report/README.md).
The PDF has a separate university cover and four content pages. This follows
the requested sample cover layout and exceeds the brief's four-page total limit.

```powershell
.\.runtime\python\python.exe scripts/build_report.py
```

To compile without rerunning experiments, use the prepared `report/figures/`
and `report/data.tex` with the main [LaTeX source](report/230145E_a02.tex).

## Implementation

1. Q1: normalized Laplacian of Gaussian and spatial/scale extrema; no Hough circles.
2. Q2: custom line RANSAC, consensus removal, custom circle RANSAC, refinement,
   and a circle-first comparison.
3. Q3: four-point selection, homography, warping, and masked blending for two
   chosen image pairs, with source attribution.
4. Q4: SIFT, brute-force matching, RANSAC homography, registration diagnostics,
   and valid-overlap difference images for every non-template PCB.

Final submission: `230145E_a02.pdf`, at most four pages, with name, index,
GitHub profile link, important code, results, comparisons, and discussion.
Commit genuine progress at each milestone; do not fabricate historical activity.
