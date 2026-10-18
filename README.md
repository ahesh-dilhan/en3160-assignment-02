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
- Published the initial repository. The report is now authored in LaTeX with a
  monochrome university title block, black typography and rules, and grayscale figures.

## Local data preparation

Keep the original `a2images.zip` beside this README and run from PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/prepare_data.ps1
```

The script validates the archive checksum and expected files before extracting
to `images/`. Original inputs remain unchanged and are excluded from Git.

## Run the experiments

Python 3.12 was used. On this Windows workspace, a project-local runtime is ready:

```powershell
.\.runtime\python\python.exe scripts/run_assignment.py --task all
.\.runtime\python\python.exe -m pytest -q tests
```

On another computer, install Python 3.12, create a virtual environment, and install
the dependencies. The runtime and assignment-provided raw images are not in Git:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/run_assignment.py --task all
```

Use `--task q1`, `q2`, `q3`, or `q4` to run one experiment. Outputs are written
under `outputs/q1` through `outputs/q4`; numerical measurements are JSON/CSV.
The Q2 experiment includes seeds 0-19 for the fitting-order comparison.

Q3 image attribution is in [assets/q3/ATTRIBUTION.md](assets/q3/ATTRIBUTION.md).
To select your own four destination corners interactively, run:

```powershell
python scripts/select_corners.py --pair 0
python scripts/select_corners.py --pair 1
```

Click top-left, top-right, bottom-right, bottom-left, then rerun Q3.

## LaTeX report

Source and build instructions: [report/README.md](report/README.md).
The four-page PDF includes the front-page university logo and title block.

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
