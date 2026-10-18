"""Hand-written RANSAC loops with geometric residuals and inlier refinement."""
from dataclasses import dataclass
import math

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize

from .common import save_json


@dataclass
class Fit:
    model: np.ndarray
    inliers: np.ndarray
    sample_indices: np.ndarray
    sample_model: np.ndarray
    trials: int
    threshold: float
    minimum_consensus: int


def generate_points(seed=0):
    # RandomState reproduces np.random.seed(seed) and Listing 1 draw order.
    rng = np.random.RandomState(seed)
    angles = rng.uniform(0, 2*np.pi, 50)
    radii = 10 + (10/16)*rng.randn(50)
    circle = np.column_stack([2+radii*np.cos(angles), 3+radii*np.sin(angles)])
    x = np.linspace(-12, 12, 50)
    line = np.column_stack([x, -x+2+rng.randn(50)])
    return np.vstack([circle, line])


def line_from_points(points):
    direction = points[1] - points[0]
    length = np.linalg.norm(direction)
    if length < 1e-10:
        raise ValueError("Coincident line sample")
    normal = np.array([-direction[1], direction[0]]) / length
    model = np.r_[normal, normal @ points[0]]
    return model if model[2] >= 0 else -model


def line_residuals(points, model):
    return np.abs(points @ model[:2] - model[2])


def refine_line(points, initial):
    centre = points.mean(axis=0)
    _, _, vt = np.linalg.svd(points-centre, full_matrices=False)
    normal = vt[-1]
    model = np.r_[normal, normal @ centre]
    return model if model[2] >= 0 else -model


def circle_from_points(points):
    shifted = points[1:] - points[0]
    scale = np.linalg.norm(shifted[0]) * np.linalg.norm(shifted[1])
    determinant = shifted[0, 0]*shifted[1, 1] - shifted[0, 1]*shifted[1, 0]
    if scale < 1e-10 or abs(determinant) / scale < 1e-5:
        raise ValueError("Collinear or near-collinear circle sample")
    offset = np.linalg.solve(2*shifted, np.sum(shifted**2, axis=1))
    centre = points[0] + offset
    return np.r_[centre, np.linalg.norm(offset)]


def circle_residuals(points, model):
    return np.abs(np.linalg.norm(points-model[:2], axis=1)-model[2])


def refine_circle(points, initial):
    def objective(model):
        delta = model[:2] - points
        distances = np.maximum(np.linalg.norm(delta, axis=1), 1e-12)
        error = distances-model[2]
        loss = np.mean(error**2)
        gradient = np.r_[2*np.mean(error[:, None]*delta/distances[:, None], axis=0),
                         -2*np.mean(error)]
        return loss, gradient
    result = minimize(objective, initial, jac=True, method="L-BFGS-B",
                      bounds=[(None, None), (None, None), (1e-8, None)],
                      options={"maxiter": 2000, "ftol": 1e-12, "gtol": 1e-8})
    if not result.success or not np.all(np.isfinite(result.x)):
        raise RuntimeError(f"Circle refinement failed: {result.message}")
    return result.x


def required_trials(confidence, inlier_fraction, sample_size):
    if not 0 < confidence < 1 or not 0 < inlier_fraction <= 1:
        raise ValueError("Invalid RANSAC probability")
    if inlier_fraction == 1:
        return 1
    return math.ceil(math.log1p(-confidence) / math.log1p(-inlier_fraction**sample_size))


def ransac(points, kind, rng, threshold=1.5, minimum_consensus=30, trials=2000):
    points = np.asarray(points, dtype=float)
    sample_size, estimate, residual, refine = {
        "line": (2, line_from_points, line_residuals, refine_line),
        "circle": (3, circle_from_points, circle_residuals, refine_circle),
    }[kind]
    if points.ndim != 2 or points.shape[1] != 2 or not np.isfinite(points).all():
        raise ValueError("Points must be a finite N x 2 array")
    if len(points) < sample_size or not sample_size <= minimum_consensus <= len(points):
        raise ValueError("Not enough points for the requested consensus")
    if threshold <= 0 or trials < 1:
        raise ValueError("Positive residual threshold and trial count required")
    best = None
    best_score = (-1, -np.inf)
    for _ in range(trials):
        sample = rng.choice(len(points), sample_size, replace=False)
        try:
            model = estimate(points[sample])
        except (ValueError, np.linalg.LinAlgError):
            continue
        errors = residual(points, model)
        inliers = errors <= threshold
        # Consensus first, then truncated squared error over every point.
        score = (int(inliers.sum()), -float(np.minimum(errors, threshold).dot(np.minimum(errors, threshold))))
        if score[0] >= minimum_consensus and score > best_score:
            best = (model, inliers, sample.copy())
            best_score = score
    if best is None:
        raise RuntimeError(f"No {kind} hypothesis reached consensus {minimum_consensus}")
    sample_model, inliers, sample = best
    model = sample_model.copy()
    # Alternate geometric fitting and inlier classification, retaining the
    # exact minimal sample and hypothesis for the required diagnostic plot.
    for _ in range(20):
        candidate = refine(points[inliers], model)
        updated = residual(points, candidate) <= threshold
        if updated.sum() < minimum_consensus:
            break
        model = candidate
        if np.array_equal(updated, inliers):
            inliers = updated
            break
        inliers = updated
    return Fit(model, inliers, sample, sample_model, trials, threshold, minimum_consensus)


def fit_sequence(points, first="line", seed=100):
    rng = np.random.default_rng(seed)
    second = "circle" if first == "line" else "line"
    first_fit = ransac(points, first, rng, minimum_consensus=35 if first == "line" else 30)
    remaining = np.flatnonzero(~first_fit.inliers)
    second_fit = ransac(points[remaining], second, rng,
                        minimum_consensus=25)
    # Return all indices and masks in the original data's coordinate system.
    second_fit.sample_indices = remaining[second_fit.sample_indices]
    expanded = np.zeros(len(points), dtype=bool)
    expanded[remaining] = second_fit.inliers
    second_fit.inliers = expanded
    return {first: first_fit, second: second_fit}


def fit_summary(points, fit, kind):
    residuals = (line_residuals if kind == "line" else circle_residuals)(points, fit.model)
    truth = np.arange(len(points)) >= 50 if kind == "line" else np.arange(len(points)) < 50
    true_positives = int(np.sum(fit.inliers & truth))
    return dict(parameters=fit.model, sample_parameters=fit.sample_model,
                sample_indices=fit.sample_indices, inlier_indices=np.flatnonzero(fit.inliers),
                inlier_count=int(fit.inliers.sum()), trials=fit.trials,
                threshold=fit.threshold, minimum_consensus=fit.minimum_consensus,
                inlier_rmse=float(np.sqrt(np.mean(residuals[fit.inliers]**2))),
                precision=true_positives/int(fit.inliers.sum()), recall=true_positives/50)


def plot_fits(points, fits, path, title):
    fig, ax = plt.subplots(figsize=(8, 8), layout="constrained")
    ax.scatter(*points.T, c="#bbc1cb", s=21, label="All 100 points")
    x = np.array([-15, 17])
    ax.plot(x, -x+2, "--", color="#687888", lw=1, label="Ground-truth line")
    ax.add_patch(plt.Circle((2, 3), 10, fill=False, linestyle="--", color="#687888", label="Ground-truth circle"))
    for kind, colour in [("line", "#cb563b"), ("circle", "#007f86")]:
        fit = fits[kind]
        ax.scatter(*points[fit.inliers].T, s=24, c=colour, label=f"{kind.title()} inliers")
        ax.scatter(*points[fit.sample_indices].T, s=110, marker="x", c=colour,
                   linewidths=2.2, label=f"Winning {kind} sample")
        for model, style, label in [(fit.sample_model, ":", f"Sample {kind}"),
                                     (fit.model, "-", f"Refined {kind}")]:
            if kind == "line":
                if abs(model[1]) > 1e-8:
                    ax.plot(x, (model[2]-model[0]*x)/model[1], style, color=colour, lw=1.8, label=label)
                else:
                    ax.axvline(model[2]/model[0], linestyle=style, color=colour, label=label)
            else:
                ax.add_patch(plt.Circle(model[:2], model[2], fill=False,
                                       linestyle=style, color=colour, lw=1.8, label=label))
    ax.set(xlim=(-15, 17), ylim=(-14, 17), xlabel="x", ylabel="y", title=title)
    ax.set_aspect("equal"); ax.grid(alpha=.15)
    ax.legend(fontsize=8, loc="upper right")
    fig.savefig(path, dpi=180); plt.close(fig)


def run(output, seed=0, comparison_seeds=20):
    output.mkdir(parents=True, exist_ok=True)
    points = generate_points(seed)
    np.savetxt(output / "points.csv", points, delimiter=",", header="x,y", comments="")
    sequences = {}
    for first in ["line", "circle"]:
        try:
            fits = fit_sequence(points, first)
            sequences[f"{first}_first"] = {k: fit_summary(points, v, k) for k, v in fits.items()}
            plot_fits(points, fits, output / f"{first}_first.png", f"{first.title()}-first RANSAC; data seed {seed}")
        except RuntimeError as error:
            sequences[f"{first}_first"] = {"error": str(error)}
    comparison = []
    for data_seed in range(comparison_seeds):
        data = generate_points(data_seed)
        row = {"data_seed": data_seed}
        for first in ["line", "circle"]:
            try:
                fits = fit_sequence(data, first)
                circle_error = float(np.linalg.norm(fits["circle"].model[:2]-[2, 3]))
                radius_error = abs(float(fits["circle"].model[2])-10)
                row[f"{first}_first"] = dict(centre_error=circle_error, radius_error=radius_error,
                    recovered_circle=circle_error < 2 and radius_error < 2,
                    line=fit_summary(data, fits["line"], "line"),
                    circle=fit_summary(data, fits["circle"], "circle"))
            except RuntimeError as error:
                row[f"{first}_first"] = {"error": str(error), "recovered_circle": False}
        comparison.append(row)
    results = dict(data_seed=seed, ransac_seed=100, threshold_line=1.5, threshold_circle=1.5,
                   trials_per_model=2000, nominal_trials_at_50_percent={
                       "line": required_trials(.99, .5, 2), "circle": required_trials(.99, .5, 3)},
                   sequences=sequences, fitting_order_comparison=comparison)
    save_json(output / "results.json", results)
    return results
