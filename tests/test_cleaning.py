import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from floodfolio.cleaning import Audit, parse_damage


class DamageParsingTests(unittest.TestCase):
    def test_source_suffixes_and_decimal_precision(self):
        cases = {"10.00K": 10000, "0.01K": 10, "1.25M": 1250000,
                 "2B": 2000000000, "2H": 200, " 3.5 k ": 3500, "75": 75}
        for token, expected in cases.items():
            with self.subTest(token=token):
                amount, status = parse_damage(token)
                self.assertEqual(amount, expected)
                self.assertEqual(status, "positive")

    def test_explicit_zero_is_distinct_from_unknown(self):
        self.assertEqual(parse_damage("0.00K"), (0.0, "zero"))
        for token in ["", "null", None, pd.NA]:
            self.assertEqual(parse_damage(token), (None, "missing"))

    def test_malformed_or_negative_values_are_not_silently_accepted(self):
        for token in ["-10K", "TBD", "1.2Q", "1K2", "inf", "$1M"]:
            self.assertEqual(parse_damage(token), (None, "invalid"))


class KeyConflictTests(unittest.TestCase):
    def test_exact_duplicate_is_removed_but_conflicting_versions_are_all_quarantined(self):
        frame = pd.DataFrame({"event_id": [1, 1, 2, 2], "amount": [10, 10, 20, 30],
                              "source_file": ["a.csv"] * 4, "source_row": [2, 3, 4, 5]})
        audit = Audit()
        result = audit.dedupe(frame, "event", ["event_id"])
        self.assertEqual(result.event_id.tolist(), [1])
        self.assertEqual(len(audit.issues), 3)
        self.assertEqual({x["rule"] for x in audit.issues}, {"exact_duplicate", "conflicting_primary_key"})


if __name__ == "__main__":
    unittest.main()
