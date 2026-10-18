# Assignment and data review

Reviewed source: `en3160_assignment_02.pdf`, EN3160 Assignment 2 on Fitting and
Alignment, Ranga Rodrigo, dated October 9, 2026. All three pages were extracted
and rendered for visual inspection, including the mathematical constraint and
both example figures. This document records requirements and proposed methods,
not completed experimental results.

## Submission requirements

- A PDF report of **four pages or less**. Extra-page penalty: two marks per page.
- Filename for this index: `230145E_a02.pdf`.
- Include the student's name and index number within the PDF. Index confirmed:
  230145E; report name is still needed.
- Include a GitHub (or other SVN) **profile link**, with regular commits showing
  work over a reasonable duration. A repository link is also useful but does not
  replace the requested profile link.
- Grading uses only the PDF: important code excerpts, image results, comparison,
  interpretation, and discussion must be self-contained there.
- No submission deadline or explicit per-question marks are stated in the PDF.

## Q1: sunflower detection

Required input: `cv.imread('images/the_berry_farms_sunflower_field.jpeg',
cv.IMREAD_REDUCED_COLOR_4)`. The original is 1440 x 1440; expected working size
is 360 x 360. Verify this when loading with OpenCV.

Required method: Laplacian of Gaussian (LoG) blob detection with scale-space
extrema. **Do not use `cv2.HoughCircles`.** Draw detected circles, give the
parameters of the largest circles, and state the sigma range.

Proposed approach:

- Build a scale-normalized response using sigma squared times the Laplacian of
  a Gaussian-smoothed image. Choose response polarity after inspecting dark
  flower centres and bright petals; document exactly what the circles detect.
- Suppress non-extrema in both image coordinates and scale; handle boundaries
  and duplicate/overlapping detections explicitly.
- For an ideal LoG blob, convert sigma to radius using sqrt(2) times sigma.
  This is a model-based radius, not a guaranteed petal boundary.
- Tune and record sigma values, spacing, response threshold, and suppression.
  Report centres, radii, and sigma in working-image pixels. If showing original
  coordinates, label their factor-of-four conversion explicitly.

Visual observations: depth creates many different apparent flower sizes; the
sky and foliage provide distractors; foreground petals are not circular and
some flowers are tilted or partially occluded. A detector should be evaluated
visually rather than claiming every circular response is a sunflower.

## Q2: line and circle fitting

Reproduce Listing 1: 100 points total, 50 from each model. Circle centre (2, 3),
radius 10, radial Gaussian noise standard deviation 10/16 = 0.625; random
angles uniform on [0, 2*pi). Line y = -x + 2, x evenly spaced from -12 to 12,
vertical Gaussian noise standard deviation 1. Set and report a random seed for
reproducibility; the listing's seed is commented out.

- **(a)** Code RANSAC yourself. Represent the line as a*x+b*y=d with
  a*a+b*b=1. Use perpendicular residual abs(a*x+b*y-d), not vertical error.
  Use two distinct points for hypotheses. Select and justify a residual
  threshold and minimum consensus. Refine accepted inliers by total least
  squares and make the sign convention consistent (for example, d >= 0).
- **(b)** Remove the best line consensus and run custom circle RANSAC on the
  remainder. Use three non-collinear points, radial residual
  abs(norm(point-centre)-radius), an explicit threshold and minimum consensus.
  Reject degenerate samples; refine using an optimizer over geometric radial
  error. Preserve indices relative to the original point set.
- **(c)** One plot must include all points, the winning minimal-sample line,
  the winning minimal-sample circle, winning samples (two line points and three
  circle points), final best-fit line and circle, and their inliers. Showing
  ground-truth models as in the reference figure helps comparison. Distinguish
  sample hypotheses from refined fits in the legend.
- **(d)** Run and discuss a circle-first comparison. Large-radius circles can
  approximate a line, so some hypotheses may claim line points. Circle-first
  can also succeed; do not claim inevitable failure. Compare results under
  declared thresholds, degeneracy rules, and random seeds.

Use p = 0.99, for example, to motivate the RANSAC trial budget through
ceil(log(1-p)/log(1-w**s)), with sample size s and estimated inlier fraction w.
Record actual budgets, thresholds, consensus counts, refined parameters, and
residual statistics. At line-circle intersections, removing line consensus can
also remove genuine circle points; discuss this limitation.

The PDF links scipy.optimize.minimize documentation and asks for section 1.1
of Boyd and Vandenberghe as background on optimization. Read those references
before implementing the refinement; they have not been reviewed in this step.
The listing imports tikzplotlib, but it is not required by the tasks themselves.

## Q3: homography compositing

Click four corners on a planar surface, compute a homography mapping the
overlay image to that surface, warp, and blend. Do this for **a couple of image
pairs of your own choice**. An optional non-technical rationale is invited.

The supplied `flag.png` and `wadham.jpg` reproduce the assignment's example;
this pair alone does not fulfill the request for multiple chosen pairs. Select
two additional suitable pairs or confirm an interpretation before finalizing.
Record asset sources, corner coordinates and ordering, and blending opacity.
Use a warped mask, not a test for non-black pixel values, so black overlay
content is preserved. Keep source and destination point ordering consistent,
reject degenerate quadrilaterals, and blend only inside the warped region.

Visual observations: Wadham is 1024 x 768 with walls on different planes. The
four destination points must describe one planar wall region, not span the
building corner. The example in Figure 2 uses the left wall. The flag is a
1920 x 960 RGB-palette PNG with a 2:1 aspect ratio.

## Q4: PCB registration and difference

Template is explicitly **AECC1.jpg**. Use `cv2.SIFT_create()` and
`cv2.BFMatcher()`; estimate the homography with RANSAC, draw feature matches,
warp each other PCB into template coordinates, and report difference images.

Required non-template targets: AAAA1, ADAD1, AECC2, AECC3, AECC4. A template
self-comparison can serve as a pipeline sanity check, but is not one of those
five target results.

Proposed approach:

- Match SIFT descriptors with L2 distance and two-neighbour ratio filtering.
  Document the ratio and homography reprojection threshold. Check descriptor
  availability, sufficient matches, inlier count/ratio, and homography validity.
- Define the homography direction explicitly: target image to template image.
  Draw inlier matches and record registration diagnostics for each target.
- Warp images and binary validity masks to template dimensions. Compute and
  display absolute differences only on valid overlap, using a consistent
  display scale. Record raw differences; any photometric normalization must be
  separately labelled and must not silently replace the required differences.
- Inspect PCB-plane alignment separately from tall components. Repeated pin
  patterns can give ambiguous matches, while background matches may mislead
  geometric estimation. Check inlier spatial coverage visually.
- **(e)** Discuss USB Type B port, capacitors, and reset button: a single
  homography models a plane, whereas component height creates parallax under
  viewpoint changes. Occlusion, shadows, specular reflections, exposure,
  component differences and residual registration error can contribute.
  A large difference alone does not establish a manufacturing defect.

Visual observations: AAAA1 has a markedly different orientation/viewpoint.
ADAD1 also differs in viewpoint, lighting, and visible reset-button appearance.
AECC2-4 are closer in framing to AECC1 but still show apparent component and
illumination changes. These are qualitative observations, not measured defects.

## Complete supplied data inventory

Dimensions are width x height. All nine images opened successfully using the
Windows image decoder and were visually inspected in a labelled contact sheet.

| Archive path | Dimensions | Uncompressed bytes | Role |
| --- | --- | ---: | --- |
| a2images/flag.png | 1920 x 960 | 9,746 | Q3 example overlay |
| a2images/the_berry_farms_sunflower_field.jpeg | 1440 x 1440 | 224,440 | Q1 input |
| a2images/wadham.jpg | 1024 x 768 | 172,032 | Q3 example destination |
| a2images/pcbs/AAAA1.jpg | 1956 x 1982 | 1,145,801 | Q4 target |
| a2images/pcbs/ADAD1.jpg | 2169 x 2754 | 2,064,825 | Q4 target |
| a2images/pcbs/AECC1.jpg | 2302 x 2730 | 2,501,320 | Q4 template |
| a2images/pcbs/AECC2.jpg | 2279 x 2729 | 2,437,850 | Q4 target |
| a2images/pcbs/AECC3.jpg | 2287 x 2731 | 2,508,239 | Q4 target |
| a2images/pcbs/AECC4.jpg | 2281 x 2731 | 2,768,585 | Q4 target |

There are no labels, calibration files, masks, code, or additional image pairs
in the archive. Q2 data must be generated from Listing 1.

Source SHA-256 checksums:

```text
en3160_assignment_02.pdf
2B9C293DADC09C50FB19AEC34E081A47DA8EA4BC986C665634C26013388CA62C
a2images.zip
FA44D5F830872A69144AA16351E0265CDB2E1AEE4F9922A8327EB12D75F4638E
```

## Implementation and report plan

1. Establish the public repository and reproducible Python environment.
2. Implement and inspect Q1 outputs; save detection parameters and figures.
3. Implement Q2 with fixed seeds; validate geometric constraints and compare
   fitting order. Save winning samples and refined models separately.
4. Choose Q3 assets and corner points; retain source attribution and composites.
5. Register all five PCB targets, inspect diagnostics, and save a difference grid.
6. Assemble a four-page report, roughly one page per question. Include concise
   code excerpts, measurements, rationale and limitations. Render and inspect
   every page before submission. Add student name and verified GitHub profile.

Commit after meaningful milestones with genuine timestamps. No algorithms
have yet been run and no measured results are claimed in this review.
