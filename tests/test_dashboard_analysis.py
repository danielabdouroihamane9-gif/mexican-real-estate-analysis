import unittest

import numpy as np
import pandas as pd

from src.dashboard.charts import (
    geographic_map_chart,
    nested_model_r_squared_chart,
    state_median_chart,
)
from src.dashboard.geographic_analysis import (
    STATE_SUMMARY_COLUMNS,
    summarize_states,
    valid_coordinate_mask,
)
from src.dashboard.price_analysis import (
    MAIN_MODEL_FORMULA,
    analyze_price_drivers,
    area_price_sample,
    calculate_area_price_correlations,
    compare_nested_models,
    fit_price_regression,
)


class GeographicAnalysisTests(unittest.TestCase):
    def test_coordinate_validity_rejects_missing_and_out_of_range_values(self):
        dataframe = pd.DataFrame(
            {
                "lat": [19.0, None, 91.0, 15.0, 0.0, float("inf")],
                "lon": [-99.0, -99.0, 0.0, 180.0, 181.0, -90.0],
            }
        )

        self.assertEqual(
            valid_coordinate_mask(dataframe).tolist(),
            [True, False, False, True, False, False],
        )

    def test_coordinate_validation_requires_both_columns(self):
        with self.assertRaisesRegex(ValueError, "lon"):
            valid_coordinate_mask(pd.DataFrame({"lat": [19.0]}))

    def test_state_summary_uses_counts_and_positive_finite_medians(self):
        dataframe = pd.DataFrame(
            {
                "state": ["B", "A", "B", "Solo", None, "A"],
                "price_usd": [100.0, 200.0, float("inf"), 1000.0, 50.0, 0.0],
                "price_per_m2": [10.0, 20.0, None, 100.0, 5.0, -1.0],
                "area_m2": [10.0, 20.0, 30.0, 40.0, 50.0, 0.0],
            }
        )

        summary = summarize_states(dataframe).set_index("state")

        self.assertEqual(summary.loc["A", "listings"], 2)
        self.assertEqual(summary.loc["A", "median_price_usd"], 200.0)
        self.assertEqual(summary.loc["A", "median_price_per_m2"], 20.0)
        self.assertEqual(summary.loc["B", "median_area_m2"], 20.0)
        self.assertIn("Solo", summary.index)
        self.assertEqual(summary.loc["Solo", "listings"], 1)
        self.assertEqual(summary.index.tolist()[0], "Solo")

    def test_state_summary_handles_empty_and_missing_state_values(self):
        dataframe = pd.DataFrame(
            {
                "state": [None, " "],
                "price_usd": [100.0, 200.0],
                "price_per_m2": [10.0, 20.0],
                "area_m2": [10.0, 20.0],
            }
        )

        summary = summarize_states(dataframe)

        self.assertTrue(summary.empty)
        self.assertEqual(summary.columns.tolist(), STATE_SUMMARY_COLUMNS)

    def test_state_summary_requires_analytical_columns(self):
        with self.assertRaisesRegex(ValueError, "area_m2"):
            summarize_states(pd.DataFrame({"state": ["Puebla"]}))

    def test_geographic_charts_include_the_available_records(self):
        map_data = pd.DataFrame(
            {
                "lat": [19.0, 20.0],
                "lon": [-99.0, -100.0],
                "state": ["Puebla", "Jalisco"],
                "property_type": ["house", "apartment"],
                "area_m2": [100.0, 120.0],
                "price_usd": [100_000.0, 150_000.0],
                "price_per_m2": [1_000.0, 1_250.0],
            }
        )
        summary = summarize_states(
            pd.DataFrame(
                {
                    "state": ["Puebla", "Jalisco"],
                    "price_usd": [100_000.0, 150_000.0],
                    "price_per_m2": [1_000.0, 1_250.0],
                    "area_m2": [100.0, 120.0],
                }
            )
        )

        map_figure = geographic_map_chart(map_data)
        state_figure = state_median_chart(
            summary,
            metric="Median listing price (USD)",
        )

        self.assertEqual(sum(len(trace.lat) for trace in map_figure.data), 2)
        self.assertEqual(len(state_figure.data[0].y), 2)


class PriceAnalysisTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(42)
        observations = np.arange(120)
        self.dataframe = pd.DataFrame(
            {
                "area_m2": np.linspace(40, 200, len(observations)),
                "state": np.take(["Puebla", "Jalisco", "Yucatán"], observations % 3),
                "property_type": np.take(
                    ["house", "apartment"], observations % 2
                ),
            }
        )
        log_price = (
            10
            + 0.005 * self.dataframe["area_m2"]
            + 0.15 * self.dataframe["state"].eq("Jalisco")
            + 0.08 * self.dataframe["property_type"].eq("house")
            + rng.normal(0, 0.12, len(observations))
        )
        self.dataframe["price_usd"] = np.exp(log_price)
        self.dataframe["price_per_m2"] = (
            self.dataframe["price_usd"] / self.dataframe["area_m2"]
        )

    def test_correlations_use_valid_positive_area_price_pairs(self):
        dataframe = pd.DataFrame(
            {
                "area_m2": [1.0, 2.0, 3.0, 0.0, None, 6.0],
                "price_usd": [10.0, 20.0, 30.0, 40.0, 50.0, float("inf")],
            }
        )

        summary = calculate_area_price_correlations(dataframe)

        self.assertEqual(summary.observations, 3)
        self.assertAlmostEqual(summary.pearson, 1.0)
        self.assertAlmostEqual(summary.spearman, 1.0)

    def test_correlations_return_unavailable_values_for_empty_sample(self):
        summary = calculate_area_price_correlations(
            pd.DataFrame({"area_m2": [0.0], "price_usd": [None]})
        )

        self.assertEqual(summary.observations, 0)
        self.assertIsNone(summary.pearson)
        self.assertIsNone(summary.spearman)

    def test_area_price_sample_preserves_original_columns(self):
        sample = area_price_sample(self.dataframe.assign(source_dataset="sample.csv"))

        self.assertEqual(len(sample), len(self.dataframe))
        self.assertIn("source_dataset", sample.columns)

    def test_regression_uses_hc3_and_excludes_invalid_incomplete_rows(self):
        invalid_rows = pd.DataFrame(
            [
                {"area_m2": 0.0, "price_usd": 50_000, "state": "Puebla", "property_type": "house"},
                {"area_m2": 90.0, "price_usd": 0.0, "state": "Puebla", "property_type": "house"},
                {"area_m2": 90.0, "price_usd": 50_000, "state": None, "property_type": "house"},
                {"area_m2": 90.0, "price_usd": 50_000, "state": "Puebla", "property_type": " "},
            ]
        )
        dataframe = pd.concat([self.dataframe, invalid_rows], ignore_index=True)

        regression = fit_price_regression(dataframe)

        self.assertEqual(regression.observations, len(self.dataframe))
        self.assertAlmostEqual(regression.area_coefficient, 0.005, delta=0.005)
        self.assertGreater(regression.area_hc3_standard_error, 0)
        self.assertLess(regression.area_ci_low, regression.area_ci_high)
        self.assertEqual(MAIN_MODEL_FORMULA, "np.log(price_usd) ~ area_m2 + C(state) + C(property_type)")

    def test_regression_rejects_insufficient_samples(self):
        dataframe = pd.DataFrame(
            {
                "area_m2": [1.0, 2.0, 3.0, 4.0],
                "price_usd": [10.0, 20.0, 30.0, 40.0],
                "state": ["A", "A", "B", "B"],
                "property_type": ["house", "apartment", "house", "apartment"],
            }
        )

        with self.assertRaisesRegex(ValueError, "More valid observations"):
            fit_price_regression(dataframe)

    def test_nested_models_use_one_sample_and_report_all_increments(self):
        model_fits, increments = compare_nested_models(self.dataframe)
        r_squared = model_fits.set_index("model_id")["r_squared"]
        changes = increments.set_index("comparison")["r_squared_change"]

        self.assertEqual(model_fits["observations"].nunique(), 1)
        self.assertEqual(model_fits["observations"].iloc[0], len(self.dataframe))
        self.assertEqual(len(model_fits), 4)
        self.assertEqual(len(increments), 4)
        self.assertAlmostEqual(
            changes["Area added to state"],
            r_squared["B"] - r_squared["A"],
        )
        self.assertAlmostEqual(
            changes["Property type added to area + state"],
            r_squared["C"] - r_squared["B"],
        )
        self.assertAlmostEqual(
            changes["Property type added to state"],
            r_squared["D"] - r_squared["A"],
        )
        self.assertAlmostEqual(
            changes["Area added to state + property type"],
            r_squared["C"] - r_squared["D"],
        )
        self.assertTrue((increments["observations"] == len(self.dataframe)).all())
        self.assertEqual(len(nested_model_r_squared_chart(model_fits).data), 1)

    def test_combined_analysis_reuses_full_model_for_regression_summary(self):
        analysis = analyze_price_drivers(self.dataframe)
        full_model = analysis.model_fits.set_index("model_id").loc["C"]

        self.assertEqual(len(analysis.correlation_sample), len(self.dataframe))
        self.assertAlmostEqual(analysis.regression.r_squared, full_model["r_squared"])
        self.assertEqual(
            analysis.regression.observations,
            full_model["observations"],
        )
        self.assertEqual(len(analysis.model_increments), 4)

    def test_nested_models_reject_missing_required_columns(self):
        with self.assertRaisesRegex(ValueError, "state"):
            compare_nested_models(self.dataframe.drop(columns=["state"]))


if __name__ == "__main__":
    unittest.main()
