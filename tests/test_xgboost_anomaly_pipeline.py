from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np

SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "train_xgboost_anomaly.py"
SPEC = importlib.util.spec_from_file_location("train_xgboost_anomaly", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_atmospheric_features_always_use_previous_month() -> None:
    targets = np.array([1, 24, 100, 995], dtype=np.int32)

    feature_indexes = MODULE._atmospheric_feature_index(targets)

    np.testing.assert_array_equal(feature_indexes, targets - 1)
    assert np.all(feature_indexes < targets)


def test_sampled_origin_never_reaches_target() -> None:
    target, origin, lag, _ = MODULE._sample_coordinates(
        np.random.default_rng(42),
        count=10_000,
        first_target=24,
        last_target=995,
    )

    np.testing.assert_array_equal(origin, target - lag)
    assert np.all(origin < target)
    assert np.all((lag >= 1) & (lag <= 24))


def test_climatology_cutoff_excludes_future_values() -> None:
    times = np.arange("2000-01", "2002-01", dtype="datetime64[M]")
    values = np.ones((24, 1, 1), dtype=np.float32)
    values[12:] = 999

    climatology = MODULE._monthly_climatology(values, times, end_index=11)

    np.testing.assert_array_equal(climatology[:, 0, 0], np.ones(12))


def test_future_test_rows_cannot_change_an_earlier_prediction_input() -> None:
    rows = np.arange(24 * 3, dtype=np.float32).reshape(24, 3)
    january_input = MODULE._test_row(rows, 0).copy()
    rows[1:] = -999_999

    np.testing.assert_array_equal(MODULE._test_row(rows, 0), january_input)


def test_test_origin_must_be_exactly_previous_month() -> None:
    targets = np.array(["2023-01", "2023-02"], dtype="datetime64[M]")
    valid_origins = np.array(["2022-12", "2023-01"], dtype="datetime64[M]")
    MODULE._validate_test_time_contract(targets, valid_origins)

    invalid_origins = np.array(["2022-12", "2023-02"], dtype="datetime64[M]")
    with np.testing.assert_raises_regex(ValueError, "T−1"):
        MODULE._validate_test_time_contract(targets, invalid_origins)
