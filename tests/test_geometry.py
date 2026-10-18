import cv2 as cv
import numpy as np
import pytest

from assignment2.blobs import detect_blobs
from assignment2.compositing import composite
from assignment2.ransac import (circle_from_points, circle_residuals, fit_sequence,
    generate_points, line_from_points, line_residuals, ransac, required_trials)
from assignment2.registration import estimate_homography, warp_and_difference


def test_log_recovers_known_disk_position_and_scale():
    yy, xx = np.mgrid[:101, :101]
    disk = ((xx-48)**2+(yy-53)**2 <= 10**2).astype(float)
    blobs, _ = detect_blobs(disk, np.geomspace(2, 15, 48), threshold=.1)
    best = max(blobs, key=lambda b: b.response)
    assert np.hypot(best.x-48, best.y-53) < 1
    assert abs(best.radius-10) < 1


def test_normalized_line_handles_vertical_geometry():
    model = line_from_points(np.array([[4., -8], [4, 12]]))
    assert np.linalg.norm(model[:2]) == pytest.approx(1)
    assert model[2] >= 0
    np.testing.assert_allclose(line_residuals(np.array([[4., 0], [7, 2]]), model), [0, 3])


def test_circle_estimator_is_stable_after_large_translation():
    points = np.array([[5., 0], [0, 5], [-5, 0]])+[1e6, -2e6]
    model = circle_from_points(points)
    np.testing.assert_allclose(model, [1e6, -2e6, 5], atol=1e-7)
    np.testing.assert_allclose(circle_residuals(points, model), 0, atol=1e-7)


def test_degenerate_circle_sample_is_rejected():
    with pytest.raises(ValueError, match="Collinear"):
        circle_from_points(np.array([[0., 0], [1, 1], [2, 2]]))


def test_custom_ransac_rejects_outliers_without_ground_truth_labels():
    rng = np.random.default_rng(42)
    x = np.linspace(-10, 10, 80)
    inliers = np.column_stack([x, 2*x+1+rng.normal(0, .08, len(x))])
    points = np.vstack([inliers, rng.uniform(-20, 20, (50, 2))])
    fit = ransac(points, "line", rng, threshold=.2, minimum_consensus=70, trials=500)
    # Evaluate prediction on independent noiseless points, not the training mask.
    held_out = np.array([[-8., -15], [0, 1], [6, 13]])
    assert line_residuals(held_out, fit.model).max() < .08
    assert fit.inliers[:80].sum() >= 77


def test_sequential_fit_keeps_indices_and_recovers_both_models():
    points = generate_points(0)
    fits = fit_sequence(points)
    assert not (fits["line"].inliers & fits["circle"].inliers).any()
    for fit in fits.values():
        assert fit.inliers.shape == (100,)
        assert np.all((fit.sample_indices >= 0) & (fit.sample_indices < 100))
    assert np.linalg.norm(fits["line"].model[:2]) == pytest.approx(1)
    assert np.linalg.norm(fits["circle"].model[:2]-[2, 3]) < .5
    assert abs(fits["circle"].model[2]-10) < .5
    assert required_trials(.99, .5, 2) == 17
    assert required_trials(.99, .5, 3) == 35


def test_black_overlay_is_content_and_outside_pixels_are_preserved():
    background = np.full((40, 50, 3), 200, np.uint8)
    overlay = np.zeros((10, 15, 3), np.uint8)
    corners = [[10, 10], [24, 10], [24, 19], [10, 19]]
    result, H, coverage = composite(background, overlay, corners, alpha=.5)
    np.testing.assert_array_equal(result[12, 12], [100]*3)
    np.testing.assert_array_equal(result[0, 0], background[0, 0])
    assert coverage[12, 12] == 1
    mapped = cv.perspectiveTransform(np.float32([[[0, 0], [14, 0], [14, 9], [0, 9]]]), H)[0]
    np.testing.assert_allclose(mapped, corners, atol=1e-5)


def test_nonconvex_destination_is_rejected():
    with pytest.raises(ValueError, match="convex"):
        composite(np.zeros((40, 40, 3), np.uint8), np.zeros((10, 10, 3), np.uint8),
                  [[2, 2], [30, 30], [30, 2], [2, 30]])


def test_ransac_homography_predicts_unseen_points_with_bad_matches():
    rng = np.random.default_rng(7)
    source = rng.uniform(0, 500, (100, 2)).astype(np.float32)
    truth = np.array([[1.1, .03, 20], [-.04, .9, 12], [.0001, -.0002, 1.]])
    destination = cv.perspectiveTransform(source[None], truth)[0]
    destination += rng.normal(0, .15, destination.shape).astype(np.float32)
    destination[:25] = rng.uniform(0, 500, (25, 2))
    H, inliers, _ = estimate_homography(source, destination, threshold=1.)
    held_out = np.float32([[[100, 150], [400, 300], [250, 75]]])
    predicted = cv.perspectiveTransform(held_out, H)
    expected = cv.perspectiveTransform(held_out, truth)
    assert np.linalg.norm(predicted-expected, axis=2).max() < .3
    assert inliers.sum() >= 70


def test_warp_difference_excludes_padding_and_identity_is_zero():
    rng = np.random.default_rng(11)
    image = rng.integers(0, 256, (40, 60, 3), dtype=np.uint8)
    _, difference, valid = warp_and_difference(image, image, np.eye(3))
    assert valid.all()
    assert not difference.any()
    translated = np.array([[1., 0, 7], [0, 1, 0], [0, 0, 1]])
    aligned, difference, valid = warp_and_difference(image, image, translated)
    assert not valid[:, :7].any()
    assert valid[:, 10:].all()
    assert not difference[~valid].any()
