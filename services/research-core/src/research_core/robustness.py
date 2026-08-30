from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum

import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from research_core.calibration import ProbabilityCalibrator
from research_core.metrics import classification_metrics


class NullKind(StrEnum):
    IID = "IID"
    AUTOCORRELATED = "AUTOCORRELATED_FEATURES_RANDOM_TARGET"
    MARKET_FACTOR = "MARKET_FACTOR"
    VOLATILITY_CLUSTERING = "VOLATILITY_CLUSTERING"
    REGIME_LOOKING = "REGIME_LOOKING"
    CROSS_SECTIONAL = "CROSS_SECTIONAL_CORRELATION"


class ExperimentDecision(StrEnum):
    NO_EDGE = "NO_EDGE"
    INCONCLUSIVE = "INCONCLUSIVE"
    CANDIDATE_EDGE = "CANDIDATE_EDGE"
    VALIDATION_REQUIRED = "VALIDATION_REQUIRED"
    SYNTHETIC_EXPECTED_EDGE = "SYNTHETIC_EXPECTED_EDGE"
    ENGINEERING_FAILURE = "ENGINEERING_FAILURE"


@dataclass(frozen=True)
class NullRun:
    seed: int
    sample_size: int
    instruments: int
    null_kind: str
    positive_rate: float
    model: str
    roc_auc: float
    pr_auc: float
    brier: float
    log_loss: float
    accuracy: float
    balanced_accuracy: float
    calibration_error: float
    baseline_roc_auc: float
    baseline_pr_auc: float
    baseline_brier: float
    baseline_log_loss: float
    brier_improvement: float
    log_loss_improvement: float


def synthetic_panel(
    *,
    seed: int,
    observations: int = 1000,
    instruments: int = 5,
    kind: NullKind = NullKind.IID,
    signal_strength: float = 0.0,
) -> pd.DataFrame:
    """Create chronological panels whose future label is independent when strength is zero."""
    rng = np.random.default_rng(seed)
    periods = max(12, int(np.ceil(observations / instruments)))
    rows = periods * instruments
    time = np.repeat(np.arange(periods), instruments)
    instrument = np.tile(np.arange(instruments), periods)
    common = rng.normal(size=periods)
    x = rng.normal(size=(rows, 8))
    if kind in {NullKind.MARKET_FACTOR, NullKind.CROSS_SECTIONAL}:
        x[:, :3] += np.repeat(common, instruments)[:, None] * (
            0.8 if kind == NullKind.MARKET_FACTOR else 1.4
        )
    if kind in {NullKind.AUTOCORRELATED, NullKind.REGIME_LOOKING, NullKind.VOLATILITY_CLUSTERING}:
        for name in range(instruments):
            loc = np.flatnonzero(instrument == name)
            for index in range(1, len(loc)):
                x[loc[index], :4] += 0.85 * x[loc[index - 1], :4]
    if kind == NullKind.VOLATILITY_CLUSTERING:
        scale = np.where((time // 25) % 2, 2.5, 0.5)
        x *= scale[:, None]
    if kind == NullKind.REGIME_LOOKING:
        x[:, 0] += np.where((time // 40) % 2, 2.0, -2.0)
    logits = signal_strength * x[:, 0]
    probability = 1 / (1 + np.exp(-logits))
    target = (rng.random(rows) < probability).astype(int)
    columns = {f"x_{i}": x[:, i] for i in range(x.shape[1])}
    return pd.DataFrame({"time": time, "instrument": instrument, **columns, "target": target}).iloc[
        :observations
    ]


def evaluate_panel(frame: pd.DataFrame, *, seed: int, kind: str = "CUSTOM") -> NullRun:
    features = [column for column in frame if column.startswith("x_")]
    times = np.sort(frame.time.unique())
    train_end = times[int(len(times) * 0.60)]
    calibration_end = times[int(len(times) * 0.80)]
    train = frame[frame.time <= train_end]
    calibration = frame[(frame.time > train_end) & (frame.time <= calibration_end)]
    test = frame[frame.time > calibration_end]
    model = make_pipeline(StandardScaler(), LogisticRegression(C=0.25, random_state=seed))
    model.fit(train[features], train.target)
    raw_calibration = model.predict_proba(calibration[features])[:, 1]
    calibrator = ProbabilityCalibrator("sigmoid").fit(raw_calibration, calibration.target)
    probability = calibrator.predict(model.predict_proba(test[features])[:, 1])
    base_probability = np.full(len(test), train.target.mean())
    metrics = classification_metrics(test.target, probability)
    baseline = classification_metrics(test.target, base_probability)
    return NullRun(
        seed=seed,
        sample_size=len(test),
        instruments=int(frame.instrument.nunique()),
        null_kind=kind,
        positive_rate=float(test.target.mean()),
        model="regularized_logistic",
        roc_auc=metrics["roc_auc"],
        pr_auc=metrics["pr_auc"],
        brier=metrics["brier"],
        log_loss=metrics["log_loss"],
        accuracy=metrics["accuracy"],
        balanced_accuracy=metrics["balanced_accuracy"],
        calibration_error=metrics["calibration_error"],
        baseline_roc_auc=baseline["roc_auc"],
        baseline_pr_auc=baseline["pr_auc"],
        baseline_brier=baseline["brier"],
        baseline_log_loss=baseline["log_loss"],
        brier_improvement=baseline["brier"] - metrics["brier"],
        log_loss_improvement=baseline["log_loss"] - metrics["log_loss"],
    )


def null_monte_carlo(
    seeds: Sequence[int],
    *,
    observations: int = 1000,
    instruments: int = 5,
    kind: NullKind = NullKind.IID,
) -> pd.DataFrame:
    return pd.DataFrame(
        asdict(
            evaluate_panel(
                synthetic_panel(
                    seed=seed, observations=observations, instruments=instruments, kind=kind
                ),
                seed=seed,
                kind=kind.value,
            )
        )
        for seed in seeds
    )


def distribution_summary(values: Sequence[float]) -> dict[str, float]:
    value = np.asarray(values, dtype=float)
    percentiles = np.quantile(value, [0.025, 0.05, 0.25, 0.5, 0.75, 0.95, 0.975])
    return {
        "mean": float(value.mean()),
        "median": float(percentiles[3]),
        "std": float(value.std(ddof=1)),
        "p2_5": float(percentiles[0]),
        "p5": float(percentiles[1]),
        "p25": float(percentiles[2]),
        "p75": float(percentiles[4]),
        "p95": float(percentiles[5]),
        "p97_5": float(percentiles[6]),
        "min": float(value.min()),
        "max": float(value.max()),
    }


def null_context(
    observed_auc: float, null_aucs: Sequence[float], *, primary_improvement: float
) -> dict[str, object]:
    values = np.asarray(null_aucs, dtype=float)
    empirical_p = float((1 + (values >= observed_auc).sum()) / (len(values) + 1))
    percentile = float((values <= observed_auc).mean() * 100)
    conclusion = (
        "NO EVIDENCE OF PREDICTIVE ADVANTAGE"
        if primary_improvement <= 0 or empirical_p > 0.05
        else "VALIDATION REQUIRED"
    )
    return {
        "observed_roc_auc": observed_auc,
        "null_percentile": percentile,
        "empirical_p": empirical_p,
        "primary_brier_improvement": primary_improvement,
        "conclusion": conclusion,
    }


def block_permutation_test(
    y: Sequence[int],
    score: Sequence[float],
    *,
    block_size: int = 5,
    permutations: int = 500,
    seed: int = 17,
) -> dict[str, object]:
    y_array, score_array = np.asarray(y), np.asarray(score)
    observed = float(roc_auc_score(y_array, score_array))
    blocks = [score_array[i : i + block_size] for i in range(0, len(score_array), block_size)]
    rng = np.random.default_rng(seed)
    null = []
    for _ in range(permutations):
        order = rng.permutation(len(blocks))
        permuted = np.concatenate([blocks[i] for i in order])[: len(y_array)]
        null.append(float(roc_auc_score(y_array, permuted)))
    null_array = np.asarray(null)
    return {
        "observed": observed,
        "empirical_p": float((1 + (null_array >= observed).sum()) / (permutations + 1)),
        "observed_percentile": float((null_array <= observed).mean()),
        "null": null,
    }


def moving_block_auc_interval(
    y: Sequence[int],
    score: Sequence[float],
    *,
    block_size: int = 5,
    samples: int = 500,
    seed: int = 17,
) -> tuple[float, float]:
    y_array, score_array = np.asarray(y), np.asarray(score)
    starts = np.arange(0, len(y_array) - block_size + 1)
    rng = np.random.default_rng(seed)
    estimates: list[float] = []
    while len(estimates) < samples:
        chosen = rng.choice(starts, size=int(np.ceil(len(y_array) / block_size)), replace=True)
        index = np.concatenate([np.arange(i, i + block_size) for i in chosen])[: len(y_array)]
        if np.unique(y_array[index]).size == 2:
            estimates.append(roc_auc_score(y_array[index], score_array[index]))
    quantiles = np.quantile(estimates, [0.025, 0.975])
    return float(quantiles[0]), float(quantiles[1])


def effective_sample_diagnostics(frame: pd.DataFrame, *, horizon: int) -> dict[str, object]:
    rows = len(frame)
    periods = int(frame.time.nunique())
    instruments = int(frame.instrument.nunique())
    target = frame.target.to_numpy(dtype=float)
    serial = float(pd.Series(target).autocorr()) if rows > 2 else 0.0
    serial = 0.0 if np.isnan(serial) else serial
    overlap_adjusted = max(1, periods // max(1, horizon))
    conservative = max(1, int(overlap_adjusted / max(1.0, 1 + 2 * max(0.0, serial))))
    warnings = []
    if horizon > 1:
        warnings.append("TARGET_OVERLAP")
    if rows > periods:
        warnings.append("CROSS_SECTIONAL_DEPENDENCE_POSSIBLE")
    if abs(serial) > 0.1:
        warnings.append("SERIAL_CORRELATION")
    if conservative < 100:
        warnings.append("INSUFFICIENT_EFFECTIVE_SAMPLE")
    return {
        "rows": rows,
        "periods": periods,
        "instruments": instruments,
        "lag1_target_correlation": serial,
        "conservative_effective_n": conservative,
        "warnings": warnings,
    }


def research_warnings(
    *,
    metrics: dict[str, float],
    baseline: dict[str, float],
    fold_aucs: Sequence[float],
    effective_n: int,
    attempts: int = 1,
) -> list[str]:
    warnings = []
    if metrics["brier"] >= baseline["brier"]:
        warnings.append("NO_BASELINE_IMPROVEMENT")
    if metrics["calibration_error"] > 0.1:
        warnings.append("POOR_CALIBRATION")
    if metrics.get("max_probability", 0.0) > 0.9 and metrics["calibration_error"] > 0.05:
        warnings.append("OVERCONFIDENT_MODEL")
    if effective_n < 100:
        warnings.append("INSUFFICIENT_SAMPLE")
    if fold_aucs and (np.std(fold_aucs) > 0.1 or min(fold_aucs) < 0.45):
        warnings.append("UNSTABLE_ACROSS_FOLDS")
    if attempts > 1:
        warnings.append("MULTIPLE_TESTING_RISK")
    return warnings


def classify_experiment(
    *,
    synthetic_planted: bool,
    engineering_ok: bool,
    primary_improvement: float,
    empirical_p: float,
    stable: bool,
) -> ExperimentDecision:
    if not engineering_ok:
        return ExperimentDecision.ENGINEERING_FAILURE
    if synthetic_planted and primary_improvement > 0 and empirical_p <= 0.05:
        return ExperimentDecision.SYNTHETIC_EXPECTED_EDGE
    if primary_improvement <= 0:
        return ExperimentDecision.NO_EDGE
    if empirical_p > 0.05 or not stable:
        return ExperimentDecision.INCONCLUSIVE
    return ExperimentDecision.VALIDATION_REQUIRED


def selection_bias_simulation(
    attempts: Sequence[int],
    *,
    repetitions: int = 500,
    test_size: int = 250,
    seed: int = 17,
) -> dict[int, dict[str, float]]:
    rng = np.random.default_rng(seed)
    output = {}
    for count in attempts:
        maxima = []
        for _ in range(repetitions):
            y = rng.integers(0, 2, test_size)
            scores = rng.normal(size=(count, test_size))
            ranks = rankdata(scores, axis=1)
            positive_count = int(y.sum())
            negative_count = test_size - positive_count
            rank_sum = ranks[:, y == 1].sum(axis=1)
            aucs = (rank_sum - positive_count * (positive_count + 1) / 2) / (
                positive_count * negative_count
            )
            maxima.append(float(aucs.max()))
        output[count] = distribution_summary(maxima)
    return output


def feature_mining_simulation(
    feature_counts: Sequence[int], *, repetitions: int = 200, test_size: int = 250, seed: int = 17
) -> dict[int, dict[str, float]]:
    """Measure the best spurious univariate AUC available from noise features."""
    return selection_bias_simulation(
        feature_counts, repetitions=repetitions, test_size=test_size, seed=seed
    )


def walk_forward_stability(
    frame: pd.DataFrame, *, folds: int = 5, minimum_train_fraction: float = 0.4, seed: int = 17
) -> dict[str, object]:
    times = np.sort(frame.time.unique())
    start = int(len(times) * minimum_train_fraction)
    boundaries = np.linspace(start, len(times), folds + 1, dtype=int)
    aucs = []
    for fold in range(folds):
        train_times = times[: boundaries[fold]]
        test_times = times[boundaries[fold] : boundaries[fold + 1]]
        if not len(test_times):
            continue
        subset = frame[frame.time.isin(np.concatenate([train_times, test_times]))].copy()
        cutoff = len(train_times)
        subset["time"] = subset.time.map(
            {value: index for index, value in enumerate(np.concatenate([train_times, test_times]))}
        )
        # evaluate_panel uses a 60/20/20 split; pad chronology so its final segment is this fold.
        subset.loc[subset.time < cutoff, "time"] = np.floor(
            subset.loc[subset.time < cutoff, "time"] * 0.8 * cutoff / max(1, cutoff)
        )
        aucs.append(evaluate_panel(subset, seed=seed + fold, kind="WALK_FORWARD").roc_auc)
    return {
        "fold_aucs": aucs,
        "mean": float(np.mean(aucs)),
        "variance": float(np.var(aucs)),
        "worst": float(np.min(aucs)),
        "best": float(np.max(aucs)),
        "positive_sign_fraction": float(np.mean(np.asarray(aucs) > 0.5)),
    }


def analogue_null_audit(
    *,
    seeds: Sequence[int],
    k_values: Sequence[int] = (10, 20, 50, 100, 200),
    observations: int = 1000,
) -> dict[int, dict[str, float]]:
    """Nearest-state outcomes on null data must average to the unconditional outcome."""
    output: dict[int, list[float]] = {k: [] for k in k_values}
    for seed in seeds:
        frame = synthetic_panel(seed=seed, observations=observations)
        features = frame.filter(like="x_").to_numpy()
        target = frame.target.to_numpy(dtype=float)
        query = features[-1]
        distance = np.linalg.norm(features[:-1] - query, axis=1)
        order = np.argsort(distance)
        baseline = float(target[:-1].mean())
        for k in k_values:
            output[k].append(float(target[:-1][order[: min(k, len(order))]].mean() - baseline))
    return {k: distribution_summary(values) for k, values in output.items()}


def signal_strength_curve(
    strengths: Sequence[float],
    seeds: Sequence[int],
    *,
    observations: int = 1000,
) -> dict[float, dict[str, float]]:
    output = {}
    for strength in strengths:
        aucs = [
            evaluate_panel(
                synthetic_panel(seed=seed, observations=observations, signal_strength=strength),
                seed=seed,
                kind="PLANTED",
            ).roc_auc
            for seed in seeds
        ]
        output[float(strength)] = distribution_summary(aucs)
    return output


def false_discovery_simulation(
    *,
    repetitions: int = 500,
    hypotheses: int = 100,
    alpha: float = 0.05,
    seed: int = 17,
    adjuster: Callable[[Sequence[float]], np.ndarray],
) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    discoveries = [
        int((adjuster(rng.random(hypotheses).tolist()) <= alpha).sum()) for _ in range(repetitions)
    ]
    return {
        "runs_with_false_discovery": float(np.mean(np.asarray(discoveries) > 0)),
        "mean_false_discoveries": float(np.mean(discoveries)),
    }
