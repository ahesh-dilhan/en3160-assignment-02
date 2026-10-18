# EN3160 Assignment 02: Fitting and Alignment

Index number: **230145E**. Intended GitHub repository: `en3160-assignment-02` (public).

This project covers scale-space blob detection, custom RANSAC model fitting,
planar image compositing, and SIFT-based PCB registration.

## Current progress

- Reviewed the complete three-page assignment, including the example figures.
- Extracted and visually inspected all nine source images.
- Recorded requirements, data properties, and the implementation plan in
  [the assignment review](docs/assignment_review.md).
- Algorithm implementation and experiment results are pending.
- GitHub publication is pending an authenticated connection.

## Local data preparation

Keep the original `a2images.zip` beside this README and run from PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/prepare_data.ps1
```

The script validates the archive checksum and expected files before extracting
to `images/`. Original inputs remain unchanged and are excluded from Git.

## Planned implementation

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
