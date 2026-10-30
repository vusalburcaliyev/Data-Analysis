import json
from pathlib import Path
import sqlite3
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from floodfolio.config import DATABASE, ROOT
from floodfolio.pipeline import verify_extracts


class ModelContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DATABASE.exists():
            raise RuntimeError("Run python run_pipeline.py before model-contract tests")
        cls.db = sqlite3.connect(DATABASE)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def scalar(self, sql):
        return self.db.execute(sql).fetchone()[0]

    def test_raw_extract_checksums(self):
        self.assertEqual(len(verify_extracts()["extracts"]), 15)

    def test_primary_and_foreign_key_integrity(self):
        self.assertEqual(self.db.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_verified_snapshot_counts(self):
        for table, expected in {"fact_event": 19191, "fact_location": 58578, "fact_fatality": 401,
                                "dim_episode": 5162, "dim_geography": 2383, "dim_date": 1827}.items():
            with self.subTest(table=table):
                self.assertEqual(self.scalar(f"SELECT COUNT(*) FROM {table}"), expected)

    def test_child_aggregation_preserves_event_grain_and_loss(self):
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM vw_event_enriched"), self.scalar("SELECT COUNT(*) FROM fact_event"))
        self.assertEqual(self.scalar("SELECT SUM(property_damage_usd) FROM vw_event_enriched"), 8780404020)

    def test_casualty_discrepancy_is_visible(self):
        self.assertEqual(self.scalar("SELECT SUM(deaths_direct) FROM fact_event"), 389)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM fact_fatality WHERE fatality_type='D'"), 391)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM vw_event_enriched WHERE deaths_direct <> direct_fatality_records"), 1)

    def test_routine_filter_does_not_modify_accounting_population(self):
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM vw_routine_event"), 18012)
        self.assertEqual(self.scalar("SELECT SUM(duration_outlier + damage_outlier) FROM vw_routine_event"), 0)
        self.assertEqual(self.scalar("SELECT SUM(property_damage_usd) FROM fact_event"), 8780404020)

    def test_reported_zero_is_not_missing(self):
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM fact_event WHERE property_damage_status='zero'"), 13478)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM fact_event WHERE property_damage_status='zero' AND property_damage_usd IS NULL"), 0)

    def test_complete_period_and_geographic_scope(self):
        self.assertEqual(self.scalar("SELECT COUNT(DISTINCT year || '-' || month) FROM fact_event"), 60)
        self.assertEqual(self.scalar("SELECT COUNT(DISTINCT state_fips) FROM dim_geography"), 51)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM dim_geography WHERE state_fips IN (60,66,72,78)"), 0)

    def test_generated_tables_reconcile(self):
        summary = json.loads((ROOT / "reports/tables/kpi_summary.json").read_text())
        self.assertEqual(summary["recorded_events"], self.scalar("SELECT COUNT(*) FROM fact_event"))
        self.assertAlmostEqual(summary["top_1pct_loss_share_pct"], 95.23509374913706, places=8)


if __name__ == "__main__":
    unittest.main()
