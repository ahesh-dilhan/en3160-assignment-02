# Saved experiment results

These are the actual outputs produced by `scripts/run_assignment.py`, included
alongside the code and report for review and reproducibility.

- **q1:** all 53 selected candidate disks in `detections.csv`, their annotated
  image and overview, and the sigma range/post-filter settings in `results.json`.
  Coordinates refer to the 360 x 360 image, not the original resolution.
- **q2:** the generated 100-point data, line-first/circle-first diagnostic plots,
  model parameters, winning samples, inlier indices, and results for data seeds
  0-19 in `results.json`.
- **q3:** for each chosen pair, the original overlay graphic, composite,
  coverage mask, selected coordinates and homography. The coordinates were
  recorded using four mouse clicks per image; the events and original-image
  checksums are saved in `assets/q3/corner_clicks.json`.
- **q4:** five complete target folders, each containing `aligned.jpg`,
  `matches.jpg`, `difference.png`, `valid_mask.png`, `overlay.jpg`, and
  `metrics.json`. The overview, combined CSV and combined JSON are also included.

Q4 difference PNGs retain raw 8-bit RGB absolute differences. Invalid overlap is
stored as zero; use the accompanying validity mask to distinguish it from a true
zero difference. The report's colour-map display clips at 100 for visual comparison;
the raw images and numerical metrics do not use that clipping.

Report figures may use different labels or drawing styles from these experimental
previews. The report's measured tables derive from these same JSON results.
