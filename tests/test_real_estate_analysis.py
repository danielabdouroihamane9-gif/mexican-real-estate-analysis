import unittest
import pandas as pd

from src.real_estate_analysis import (
    build_processed_datasets,
    UNRESOLVED_MXN_TO_USD_RATE,
    normalize_text,
    find_cross_source_overlaps,
    parse_lat_lon,
    parse_usd_price,
    state_from_place,
)


class CleaningHelperTests(unittest.TestCase):
    def test_parse_usd_price(self):
        self.assertAlmostEqual(parse_usd_price("$67,965.56"), 67965.56)

    def test_parse_lat_lon(self):
        self.assertEqual(parse_lat_lon("19.52589,-99.151703"), (19.52589, -99.151703))
        lat, lon = parse_lat_lon(None)
        self.assertTrue(lat != lat and lon != lon)

    def test_state_from_place(self):
        value = "|México|Estado de México|Toluca|Toluca de Lerdo|"
        self.assertEqual(state_from_place(value), "Estado de México")

    def test_text_normalization(self):
        self.assertEqual(normalize_text("  Nuevo León  "), "Nuevo León")

    def test_processed_datasets(self):
        combined, geospatial = build_processed_datasets()
        self.assertIn("source_dataset", combined.columns)
        self.assertIn("price_mxn", combined.columns)
        self.assertIn("conversion_rate_mxn_per_usd", combined.columns)
        self.assertIn("price_per_m2", combined.columns)
        self.assertEqual(combined.duplicated().sum(), 0)
        core_columns = ["source_dataset", "property_type", "state", "area_m2", "price_usd", "price_per_m2"]
        self.assertFalse(combined[core_columns].isna().any().any())
        self.assertTrue(combined["area_m2"].gt(0).all())
        self.assertTrue(combined["price_usd"].gt(0).all())
        self.assertEqual(geospatial.duplicated().sum(), 0)
        geo_core = ["source_dataset","property_type","state","lat","lon","area_m2","price_usd","price_per_m2"]
        self.assertFalse(geospatial[geo_core].isna().any().any())

    def test_mxn_provenance_and_conversion(self):
        combined, _ = build_processed_datasets()
        mxn = combined.loc[
            combined["source_dataset"] == "mexico-real-estate-2.csv"
        ]
        self.assertTrue(mxn["price_mxn"].gt(0).all())
        self.assertTrue(
            mxn["conversion_rate_mxn_per_usd"].eq(UNRESOLVED_MXN_TO_USD_RATE).all()
        )
        expected = mxn["price_mxn"] / UNRESOLVED_MXN_TO_USD_RATE
        self.assertTrue((mxn["price_usd"].round(12) == expected.round(12)).all())

    def test_audit_report_schema(self):
        combined, _ = build_processed_datasets()
        import json
        from src.real_estate_analysis import PROCESSED_DATA_DIR
        with open(PROCESSED_DATA_DIR / "cleaning_audit.json", encoding="utf-8") as handle:
            audit = json.load(handle)
        self.assertEqual(set(audit), {
            "currency_assumption", "sources", "cross_source_potential_overlaps",
            "final_counts",
        })
        self.assertEqual(audit["final_counts"]["analytical_rows"], len(combined))
        self.assertEqual(
            {item["source_dataset"] for item in audit["sources"]},
            {
                "mexico-real-estate-1.csv",
                "mexico-real-estate-2.csv",
                "mexico-real-estate-3.csv",
            },
        )

    def test_configurable_mxn_rate(self):
        combined, _ = build_processed_datasets(mxn_rate=20)
        mxn = combined.loc[
            combined["source_dataset"] == "mexico-real-estate-2.csv"
        ]
        self.assertTrue(mxn["conversion_rate_mxn_per_usd"].eq(20).all())
        self.assertTrue((mxn["price_usd"] == mxn["price_mxn"] / 20).all())
        build_processed_datasets()

    def test_cross_source_overlap_requires_two_sources(self):
        data = pd.DataFrame([
            {"property_type": "house", "state": "Puebla", "area_m2": 100.0, "price_usd": 10000.0, "source_dataset": "a.csv"},
            {"property_type": "house", "state": "Puebla", "area_m2": 100.0, "price_usd": 10000.0, "source_dataset": "b.csv"},
            {"property_type": "apartment", "state": "Puebla", "area_m2": 80.0, "price_usd": 8000.0, "source_dataset": "a.csv"},
            {"property_type": "apartment", "state": "Puebla", "area_m2": 80.0, "price_usd": 8000.0, "source_dataset": "a.csv"},
        ])
        result = find_cross_source_overlaps(data)
        self.assertEqual(result["distinct_matching_key_count"], 1)
        self.assertEqual(result["rows_belonging_to_matching_keys"], 2)
        self.assertEqual(result["source_datasets_involved"], ["a.csv", "b.csv"])

    def test_cross_source_overlap_no_matches(self):
        data = pd.DataFrame([
            {"property_type": "house", "state": "Puebla", "area_m2": 100.0, "price_usd": 10000.0, "source_dataset": "a.csv"},
            {"property_type": "house", "state": "Puebla", "area_m2": 100.0, "price_usd": 10000.0, "source_dataset": "a.csv"},
        ])
        result = find_cross_source_overlaps(data)
        self.assertEqual(result["distinct_matching_key_count"], 0)
        self.assertEqual(result["rows_belonging_to_matching_keys"], 0)
        self.assertEqual(result["source_datasets_involved"], [])

    def test_audit_names_standardized_duplicate_metric(self):
        combined, _ = build_processed_datasets()
        import json
        from src.real_estate_analysis import PROCESSED_DATA_DIR
        with open(PROCESSED_DATA_DIR / "cleaning_audit.json", encoding="utf-8") as handle:
            audit = json.load(handle)
        for source in audit["sources"]:
            self.assertIn("raw_exact_duplicate_rows", source)
            self.assertIn("duplicate_standardized_keys_removed_within_source", source)
            self.assertNotIn("exact_duplicates_removed_within_source", source)


if __name__ == "__main__":
    unittest.main()
