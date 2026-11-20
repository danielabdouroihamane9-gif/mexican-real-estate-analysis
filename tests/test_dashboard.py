import tempfile
import unittest
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from src.dashboard.data_loader import (
    DashboardDataError,
    load_processed_datasets,
)
from src.dashboard.filtering import (
    available_category_values,
    filter_properties,
    numeric_range_bounds,
)
from src.dashboard.metrics import (
    aggregate_property_types,
    aggregate_states,
    calculate_market_metrics,
)


class DashboardDataLoaderTests(unittest.TestCase):
    def setUp(self):
        load_processed_datasets.clear()

    def tearDown(self):
        load_processed_datasets.clear()

    def _write_pair(self, directory: Path, analytical: pd.DataFrame, geospatial: pd.DataFrame):
        analytical_path = directory / "analytical.csv"
        geospatial_path = directory / "geospatial.csv"
        analytical.to_csv(analytical_path, index=False)
        geospatial.to_csv(geospatial_path, index=False)
        return analytical_path, geospatial_path

    def _valid_frames(self):
        common = {
            "source_dataset": ["source.csv"],
            "property_type": ["house"],
            "state": ["Puebla"],
            "area_m2": [100.0],
            "price_usd": [10000.0],
            "price_mxn": [None],
            "conversion_rate_mxn_per_usd": [None],
            "price_per_m2": [100.0],
        }
        analytical = pd.DataFrame(common)
        geospatial = analytical.assign(lat=[19.0], lon=[-98.0])
        return analytical, geospatial

    def test_loads_both_processed_datasets(self):
        analytical, geospatial = self._valid_frames()
        with tempfile.TemporaryDirectory() as temporary_directory:
            paths = self._write_pair(Path(temporary_directory), analytical, geospatial)
            loaded_analytical, loaded_geospatial = load_processed_datasets(*paths)
        self.assertEqual(loaded_analytical.shape, (1, 8))
        self.assertEqual(loaded_geospatial.shape, (1, 10))

    def test_missing_file_has_actionable_error(self):
        analytical, geospatial = self._valid_frames()
        with tempfile.TemporaryDirectory() as temporary_directory:
            analytical_path, _ = self._write_pair(
                Path(temporary_directory), analytical, geospatial
            )
            missing_path = Path(temporary_directory) / "missing.csv"
            with self.assertRaisesRegex(DashboardDataError, "Run `python -m src.real_estate_analysis`"):
                load_processed_datasets(analytical_path, missing_path)

    def test_missing_columns_are_rejected(self):
        analytical, geospatial = self._valid_frames()
        del analytical["state"]
        with tempfile.TemporaryDirectory() as temporary_directory:
            paths = self._write_pair(Path(temporary_directory), analytical, geospatial)
            with self.assertRaisesRegex(DashboardDataError, "state"):
                load_processed_datasets(*paths)

    def test_empty_dataset_is_rejected(self):
        analytical, geospatial = self._valid_frames()
        with tempfile.TemporaryDirectory() as temporary_directory:
            analytical_path, geospatial_path = self._write_pair(
                Path(temporary_directory), analytical, geospatial
            )
            analytical.iloc[0:0].to_csv(analytical_path, index=False)
            with self.assertRaisesRegex(DashboardDataError, "empty"):
                load_processed_datasets(analytical_path, geospatial_path)

    def test_real_processed_datasets_have_valid_integrity(self):
        analytical, geospatial = load_processed_datasets()
        self.assertFalse(analytical.empty)
        self.assertFalse(geospatial.empty)
        self.assertTrue(analytical["area_m2"].gt(0).all())
        self.assertTrue(analytical["price_usd"].gt(0).all())
        self.assertTrue(geospatial["lat"].between(-90, 90).all())
        self.assertTrue(geospatial["lon"].between(-180, 180).all())

    def test_market_metrics_are_calculated_from_input(self):
        dataframe = pd.DataFrame(
            {
                "state": ["Puebla", "Jalisco", "Puebla"],
                "price_usd": [100_000, 300_000, 200_000],
                "area_m2": [100, 200, 300],
                "price_per_m2": [1_000, 1_500, 2_000],
            }
        )

        metrics = calculate_market_metrics(dataframe)

        self.assertEqual(metrics.total_records, 3)
        self.assertEqual(metrics.state_count, 2)
        self.assertEqual(metrics.median_price_usd, 200_000)
        self.assertEqual(metrics.median_area_m2, 200)
        self.assertEqual(metrics.median_price_per_m2, 1_500)

    def test_market_metrics_ignore_missing_and_non_numeric_values(self):
        dataframe = pd.DataFrame(
            {
                "state": ["Puebla", None, "Puebla"],
                "price_usd": [100_000, None, "not a price"],
                "area_m2": [100, float("inf"), None],
                "price_per_m2": [1_000, None, 2_000],
            }
        )

        metrics = calculate_market_metrics(dataframe)

        self.assertEqual(metrics.total_records, 3)
        self.assertEqual(metrics.state_count, 1)
        self.assertEqual(metrics.median_price_usd, 100_000)
        self.assertEqual(metrics.median_area_m2, 100)
        self.assertEqual(metrics.median_price_per_m2, 1_500)

    def test_market_metrics_handle_empty_datasets(self):
        metrics = calculate_market_metrics(
            pd.DataFrame(
                columns=["state", "price_usd", "area_m2", "price_per_m2"]
            )
        )

        self.assertEqual(metrics.total_records, 0)
        self.assertEqual(metrics.state_count, 0)
        self.assertIsNone(metrics.median_price_usd)
        self.assertIsNone(metrics.median_area_m2)
        self.assertIsNone(metrics.median_price_per_m2)

    def test_market_metrics_handle_missing_columns(self):
        metrics = calculate_market_metrics(pd.DataFrame({"property_type": ["house"]}))

        self.assertEqual(metrics.state_count, 0)
        self.assertIsNone(metrics.median_price_usd)
        self.assertIsNone(metrics.median_area_m2)
        self.assertIsNone(metrics.median_price_per_m2)

    def test_property_type_aggregation_omits_missing_categories(self):
        counts = aggregate_property_types(
            pd.DataFrame(
                {"property_type": ["house", "apartment", "house", None, "land"]}
            )
        )

        self.assertEqual(
            counts.to_dict("records"),
            [
                {"property_type": "house", "listings": 2},
                {"property_type": "apartment", "listings": 1},
                {"property_type": "land", "listings": 1},
            ],
        )

    def test_state_aggregation_uses_existing_values_and_handles_empty_data(self):
        counts = aggregate_states(
            pd.DataFrame({"state": ["Puebla", "Jalisco", "Puebla", None]})
        )
        empty_counts = aggregate_states(pd.DataFrame(columns=["state"]))

        self.assertEqual(
            counts.to_dict("records"),
            [
                {"state": "Puebla", "listings": 2},
                {"state": "Jalisco", "listings": 1},
            ],
        )
        self.assertEqual(list(empty_counts.columns), ["state", "listings"])
        self.assertTrue(empty_counts.empty)

    def test_home_uses_the_processed_dataset_loader(self):
        analytical, _ = load_processed_datasets()
        home_page = Path(__file__).resolve().parents[1] / "app" / "Home.py"

        app = AppTest.from_file(str(home_page), default_timeout=30).run()

        self.assertEqual(len(app.exception), 0)
        displayed_metrics = {metric.label: metric.value for metric in app.metric}
        self.assertEqual(
            displayed_metrics["Property records"],
            f"{len(analytical):,}",
        )
        self.assertEqual(len(app.get("plotly_chart")), 4)

    def test_market_explorer_updates_all_outputs_for_a_state_filter(self):
        analytical, _ = load_processed_datasets()
        state = available_category_values(analytical, "state")[0]
        property_types = available_category_values(analytical, "property_type")
        expected = filter_properties(
            analytical,
            states=[state],
            property_types=property_types,
            area_range=numeric_range_bounds(analytical, "area_m2"),
            price_range=numeric_range_bounds(analytical, "price_usd"),
        )
        explorer_page = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "pages"
            / "1_Market_Explorer.py"
        )

        app = AppTest.from_file(str(explorer_page), default_timeout=30).run()
        app.multiselect(key="explorer_states").set_value([state]).run()

        self.assertEqual(len(app.exception), 0)
        displayed_metrics = {metric.label: metric.value for metric in app.metric}
        self.assertEqual(displayed_metrics["Listings"], f"{len(expected):,}")
        self.assertEqual(len(app.get("plotly_chart")), 3)
        self.assertEqual(len(app.dataframe), 1)
        self.assertEqual(len(app.get("download_button")), 1)


class DashboardFilteringTests(unittest.TestCase):
    def setUp(self):
        self.dataframe = pd.DataFrame(
            {
                "state": ["Puebla", "Jalisco", "Puebla", "Yucatán"],
                "property_type": ["house", "apartment", "apartment", "house"],
                "area_m2": [100.0, 80.0, 150.0, 200.0],
                "price_usd": [100_000.0, 120_000.0, 180_000.0, 300_000.0],
                "price_per_m2": [1_000.0, 1_500.0, 1_200.0, 1_500.0],
            }
        )

    def test_state_filter(self):
        result = filter_properties(self.dataframe, states=["Puebla"])

        self.assertEqual(result.index.tolist(), [0, 2])
        self.assertEqual(set(result["state"]), {"Puebla"})

    def test_property_type_filter(self):
        result = filter_properties(self.dataframe, property_types=["apartment"])

        self.assertEqual(result.index.tolist(), [1, 2])
        self.assertEqual(set(result["property_type"]), {"apartment"})

    def test_area_filter_includes_bounds(self):
        result = filter_properties(self.dataframe, area_range=(100.0, 150.0))

        self.assertEqual(result.index.tolist(), [0, 2])

    def test_price_filter_includes_bounds(self):
        result = filter_properties(self.dataframe, price_range=(120_000.0, 180_000.0))

        self.assertEqual(result.index.tolist(), [1, 2])

    def test_combined_filters_apply_to_the_same_rows(self):
        result = filter_properties(
            self.dataframe,
            states=["Puebla", "Yucatán"],
            property_types=["house"],
            area_range=(100.0, 200.0),
            price_range=(100_000.0, 250_000.0),
        )

        self.assertEqual(result.index.tolist(), [0])

    def test_empty_category_selection_returns_no_rows(self):
        result = filter_properties(self.dataframe, states=[])

        self.assertTrue(result.empty)
        self.assertListEqual(result.columns.tolist(), self.dataframe.columns.tolist())

    def test_missing_and_invalid_values_are_excluded_by_active_filters(self):
        dataframe = pd.DataFrame(
            {
                "state": ["Puebla", None, "Jalisco", "Yucatán"],
                "property_type": ["house", "house", None, "apartment"],
                "area_m2": [100.0, None, "invalid", float("inf")],
                "price_usd": [10_000.0, 20_000.0, 30_000.0, float("-inf")],
            }
        )

        result = filter_properties(
            dataframe,
            states=["Puebla", "Jalisco", "Yucatán"],
            property_types=["house", "apartment"],
            area_range=(0.0, 200.0),
            price_range=(0.0, 50_000.0),
        )

        self.assertEqual(result.index.tolist(), [0])

    def test_unfiltered_result_is_a_copy(self):
        result = filter_properties(self.dataframe)

        self.assertEqual(result.index.tolist(), self.dataframe.index.tolist())
        self.assertIsNot(result, self.dataframe)

    def test_filter_options_and_bounds_ignore_missing_invalid_values(self):
        dataframe = pd.DataFrame(
            {
                "state": ["Puebla", None, "Jalisco", " "],
                "area_m2": [100.0, None, "invalid", float("inf")],
            }
        )

        self.assertEqual(available_category_values(dataframe, "state"), ["Jalisco", "Puebla"])
        self.assertEqual(numeric_range_bounds(dataframe, "area_m2"), (100.0, 100.0))
        self.assertIsNone(
            numeric_range_bounds(pd.DataFrame({"area_m2": ["invalid", None]}), "area_m2")
        )

    def test_numeric_bounds_keep_valid_extreme_values(self):
        bounds = numeric_range_bounds(
            pd.DataFrame(
                {
                    "price_usd": [
                        50_000.0,
                        100_000.0,
                        5_000_000.0,
                        0.0,
                        -1.0,
                        float("inf"),
                    ]
                }
            ),
            "price_usd",
        )

        self.assertEqual(bounds, (50_000.0, 5_000_000.0))

    def test_invalid_ranges_raise_clear_errors(self):
        with self.assertRaisesRegex(ValueError, "lower area_m2 bound"):
            filter_properties(self.dataframe, area_range=(200.0, 100.0))

    def test_filtering_does_not_change_source_dataframe(self):
        before = self.dataframe.copy(deep=True)

        filter_properties(self.dataframe, states=["Puebla"], price_range=(0.0, 200_000.0))

        pd.testing.assert_frame_equal(self.dataframe, before)


if __name__ == "__main__":
    unittest.main()
