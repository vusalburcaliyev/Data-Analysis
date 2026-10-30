from __future__ import annotations

import hashlib
import json
import sqlite3

import pandas as pd

from .cleaning import Audit, clean_events, clean_children, read_raw
from .config import ROOT, PROCESSED, EXPORTS, DATABASE


def verify_extracts() -> dict:
    manifest = json.loads((ROOT / "data/sources.lock.json").read_text())
    for item in manifest["extracts"]:
        path = ROOT / item["path"]
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != item["sha256"]:
            raise ValueError(f"Raw extract changed: {item['path']}")
    return manifest


def main():
    manifest = verify_extracts()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    EXPORTS.mkdir(parents=True, exist_ok=True)
    audit = Audit()
    raw_events, raw_locations, raw_fatalities = (read_raw(t) for t in ["details", "locations", "fatalities"])
    events, geography, episodes, thresholds = clean_events(raw_events, audit)
    locations = clean_children(raw_locations, "location", events, audit)
    fatalities = clean_children(raw_fatalities, "fatality", events, audit)
    for fatality_type, summary_column in [("D", "deaths_direct"), ("I", "deaths_indirect")]:
        child_counts = fatalities.loc[fatalities.fatality_type.eq(fatality_type)].groupby("event_id").size()
        differences = events.set_index("event_id")[summary_column] - child_counts.reindex(events.event_id, fill_value=0).to_numpy()
        mismatch_ids = set(differences[differences.ne(0)].index.astype(str))
        audit.add(raw_events, raw_events.event_id.isin(mismatch_ids), "event", "fatality_summary_mismatch", summary_column,
                  "retain_both_sources_use_summary_for_headline", "review")
    dates = pd.DataFrame({"calendar_date": pd.date_range("2020-01-01", "2024-12-31")})
    dates["date_key"] = dates.calendar_date.dt.strftime("%Y%m%d").astype(int)
    dates["year"], dates["month"] = dates.calendar_date.dt.year, dates.calendar_date.dt.month
    dates["month_name"], dates["quarter"] = dates.calendar_date.dt.month_name(), dates.calendar_date.dt.quarter
    dates["day_of_week"] = dates.calendar_date.dt.day_name()
    dates["is_weekend"] = dates.calendar_date.dt.dayofweek.ge(5).astype(int)
    dates["calendar_date"] = dates.calendar_date.dt.strftime("%Y-%m-%d")
    issues = pd.DataFrame(audit.issues, columns=["issue_id", "table_name", "event_id", "source_file", "source_row", "rule", "column_name", "raw_value", "action", "severity"])
    frames = {"dim_date": dates, "dim_geography": geography, "dim_episode": episodes,
              "fact_event": events, "fact_location": locations, "fact_fatality": fatalities,
              "data_issue": issues}
    # Replace only this generated database. Source extracts and source lock are immutable.
    DATABASE.unlink(missing_ok=True)
    with sqlite3.connect(DATABASE) as conn:
        conn.executescript((ROOT / "sql/00_schema.sql").read_text())
        for name, frame in frames.items():
            frame.to_sql(name, conn, if_exists="append", index=False)
        violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"Foreign-key violations: {violations[:5]}")
        if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("SQLite integrity check failed")
    for name, frame in frames.items():
        frame.to_csv(PROCESSED / f"{name}.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    issues.to_csv(EXPORTS / "data_issues.csv", index=False)
    pd.DataFrame(audit.steps).to_csv(EXPORTS / "cleaning_waterfall.csv", index=False)
    summary = {
        "source_retrieved_at_utc": manifest["retrieved_at_utc"],
        "raw_rows": {"details": len(raw_events), "locations": len(raw_locations), "fatalities": len(raw_fatalities)},
        "model_rows": {name: len(frame) for name, frame in frames.items()},
        "outlier_thresholds": thresholds,
        "audit_issue_count": len(issues),
        "rules": issues.groupby(["severity", "rule"]).size().reset_index(name="records").to_dict("records"),
    }
    (EXPORTS / "pipeline_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
