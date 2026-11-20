"""Reusable correlation and regression calculations for listing prices."""

from dataclasses import dataclass
import math

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.regression.linear_model import RegressionResultsWrapper


MAIN_MODEL_FORMULA = (
    "np.log(price_usd) ~ area_m2 + C(state) + C(property_type)"
)
MODEL_SPECIFICATIONS = (
    ("A", "State only", "np.log(price_usd) ~ C(state)"),
    ("B", "Area + state", "np.log(price_usd) ~ area_m2 + C(state)"),
    (
        "C",
        "Area + state + property type",
        "np.log(price_usd) ~ area_m2 + C(state) + C(property_type)",
    ),
    (
        "D",
        "State + property type",
        "np.log(price_usd) ~ C(state) + C(property_type)",
    ),
)


@dataclass(frozen=True)
class CorrelationSummary:
    observations: int
    pearson: float | None
    spearman: float | None


@dataclass(frozen=True)
class RegressionSummary:
    observations: int
    r_squared: float
    adjusted_r_squared: float
    area_coefficient: float
    area_hc3_standard_error: float
    area_ci_low: float
    area_ci_high: float
    area_associated_percent: float


@dataclass(frozen=True)
class PriceDriverAnalysis:
    correlation_sample: pd.DataFrame
    correlations: CorrelationSummary
    regression: RegressionSummary
    model_fits: pd.DataFrame
    model_increments: pd.DataFrame


def area_price_sample(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return records with finite, positive area and price values."""

    _require_columns(dataframe, {"area_m2", "price_usd"})
    sample = dataframe.copy()
    for column in ("area_m2", "price_usd"):
        values = pd.to_numeric(sample[column], errors="coerce")
        values = values.replace([float("inf"), float("-inf")], pd.NA)
        sample[column] = values

    valid = (
        sample["area_m2"].gt(0)
        & sample["price_usd"].gt(0)
        & sample["area_m2"].notna()
        & sample["price_usd"].notna()
    )
    return sample.loc[valid].copy()


def calculate_area_price_correlations(
    dataframe: pd.DataFrame,
) -> CorrelationSummary:
    """Calculate Pearson and Spearman correlations on valid area-price pairs."""

    sample = area_price_sample(dataframe)
    return _calculate_correlations(sample)


def analyze_price_drivers(dataframe: pd.DataFrame) -> PriceDriverAnalysis:
    """Calculate all Price Drivers outputs while fitting the nested models once."""

    correlation_sample = area_price_sample(dataframe)
    correlations = _calculate_correlations(correlation_sample)
    regression_sample = _regression_sample(dataframe)
    _validate_model_sample(regression_sample)
    fitted_models = _fit_nested_models(regression_sample)
    model_fits, model_increments = _summarize_nested_models(fitted_models)
    regression = _regression_summary(fitted_models["C"])
    return PriceDriverAnalysis(
        correlation_sample=correlation_sample,
        correlations=correlations,
        regression=regression,
        model_fits=model_fits,
        model_increments=model_increments,
    )


def _calculate_correlations(sample: pd.DataFrame) -> CorrelationSummary:
    if len(sample) < 2:
        return CorrelationSummary(len(sample), None, None)

    pearson = sample["area_m2"].corr(sample["price_usd"], method="pearson")
    spearman = sample["area_m2"].corr(sample["price_usd"], method="spearman")
    return CorrelationSummary(
        observations=len(sample),
        pearson=_finite_or_none(pearson),
        spearman=_finite_or_none(spearman),
    )


def fit_price_regression(dataframe: pd.DataFrame) -> RegressionSummary:
    """Fit the notebook's full log-price model with HC3 robust uncertainty."""

    sample = _regression_sample(dataframe)
    _validate_model_sample(sample)
    result = smf.ols(MAIN_MODEL_FORMULA, data=sample).fit(cov_type="HC3")
    return _regression_summary(result)


def _regression_summary(result: RegressionResultsWrapper) -> RegressionSummary:
    area_interval = result.conf_int().loc["area_m2"]
    coefficient = float(result.params["area_m2"])
    return RegressionSummary(
        observations=int(result.nobs),
        r_squared=float(result.rsquared),
        adjusted_r_squared=float(result.rsquared_adj),
        area_coefficient=coefficient,
        area_hc3_standard_error=float(result.bse["area_m2"]),
        area_ci_low=float(area_interval.iloc[0]),
        area_ci_high=float(area_interval.iloc[1]),
        area_associated_percent=float((np.exp(coefficient) - 1) * 100),
    )


def compare_nested_models(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fit the four notebook specifications on one common complete-case sample."""

    sample = _regression_sample(dataframe)
    _validate_model_sample(sample)
    fitted_models = _fit_nested_models(sample)
    return _summarize_nested_models(fitted_models)


def _fit_nested_models(
    sample: pd.DataFrame,
) -> dict[str, RegressionResultsWrapper]:
    fitted_models = {}
    for model_id, _, formula in MODEL_SPECIFICATIONS:
        fitted_models[model_id] = smf.ols(formula, data=sample).fit(cov_type="HC3")
    return fitted_models


def _summarize_nested_models(
    fitted_models: dict[str, RegressionResultsWrapper],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    model_rows = []
    for model_id, label, formula in MODEL_SPECIFICATIONS:
        result = fitted_models[model_id]
        model_rows.append(
            {
                "model_id": model_id,
                "model": label,
                "formula": formula,
                "observations": int(result.nobs),
                "r_squared": float(result.rsquared),
                "adjusted_r_squared": float(result.rsquared_adj),
            }
        )

    model_fits = pd.DataFrame(model_rows)
    if model_fits["observations"].nunique() != 1:
        raise ValueError("Nested models must use the same observations for comparison.")

    comparisons = (
        ("Area added to state", "A", "B"),
        ("Property type added to area + state", "B", "C"),
        ("Property type added to state", "A", "D"),
        ("Area added to state + property type", "D", "C"),
    )
    increment_rows = []
    for label, reduced_id, expanded_id in comparisons:
        reduced = fitted_models[reduced_id]
        expanded = fitted_models[expanded_id]
        if int(reduced.nobs) != int(expanded.nobs):
            raise ValueError(
                f"Models {reduced_id} and {expanded_id} use different samples."
            )
        increment_rows.append(
            {
                "comparison": label,
                "reduced_model": reduced_id,
                "expanded_model": expanded_id,
                "observations": int(expanded.nobs),
                "r_squared_change": float(expanded.rsquared - reduced.rsquared),
            }
        )
    return model_fits, pd.DataFrame(increment_rows)


def _regression_sample(dataframe: pd.DataFrame) -> pd.DataFrame:
    required_columns = {"area_m2", "price_usd", "state", "property_type"}
    _require_columns(dataframe, required_columns)
    sample = area_price_sample(dataframe)
    state = sample["state"].astype("string")
    property_type = sample["property_type"].astype("string")
    has_state = (state.notna() & state.str.strip().ne("")).fillna(False)
    has_property_type = (
        property_type.notna() & property_type.str.strip().ne("")
    ).fillna(False)
    return sample.loc[has_state & has_property_type].copy()


def _validate_model_sample(sample: pd.DataFrame) -> None:
    if sample.empty:
        raise ValueError("No complete valid observations are available for regression.")
    if sample["area_m2"].nunique() < 2:
        raise ValueError("Property area must vary to estimate its price association.")

    parameter_count = (
        2
        + max(sample["state"].nunique() - 1, 0)
        + max(sample["property_type"].nunique() - 1, 0)
    )
    if len(sample) <= parameter_count:
        raise ValueError(
            "More valid observations than model parameters are required for "
            "regression and HC3 standard errors."
        )


def _require_columns(dataframe: pd.DataFrame, required: set[str]) -> None:
    missing = required.difference(dataframe.columns)
    if missing:
        raise ValueError(
            "Analysis data is missing required columns: " + ", ".join(sorted(missing))
        )


def _finite_or_none(value: float) -> float | None:
    return float(value) if math.isfinite(float(value)) else None
