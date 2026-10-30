"""Execute reviewable SQL and reconcile independent pandas calculations."""
from __future__ import annotations

import json
import math
import sqlite3

import numpy as np
import pandas as pd

from .config import ROOT, DATABASE, EXPORTS


def clean_json(value):
    if isinstance(value, dict):
        return {str(k): clean_json(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [clean_json(x) for x in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def main():
    tables = {}
    with sqlite3.connect(DATABASE) as connection:
        for path in sorted((ROOT / "sql").glob("[0-9][0-9]_*.sql")):
            if path.name.startswith("00_"):
                continue
            name = path.stem[3:]
            frame = pd.read_sql_query(path.read_text(), connection)
            frame.to_csv(EXPORTS / f"{name}.csv", index=False)
            tables[name] = frame
        events = pd.read_sql_query("SELECT * FROM vw_event_enriched ORDER BY event_id", connection)
        routine = pd.read_sql_query("SELECT * FROM vw_routine_event ORDER BY event_id", connection)
        fatalities = pd.read_sql_query("SELECT * FROM fact_fatality", connection)
        # A measured demonstration of the fan-out failure the production model prevents.
        naive = pd.read_sql_query("""
            SELECT COUNT(*) AS joined_rows, SUM(e.property_damage_usd) AS joined_damage_usd
            FROM fact_event e LEFT JOIN fact_location l USING(event_id)
            LEFT JOIN fact_fatality f USING(event_id)
        """, connection).iloc[0]
    head = tables["headline_kpis"].iloc[0].to_dict()
    n = len(events)
    # Independent cross-checks use different aggregation paths than the headline SQL.
    assert n == head["recorded_events"] == events.event_id.nunique()
    assert np.isclose(events.property_damage_usd.sum(), head["reported_property_damage_usd"])
    assert int(events.deaths_direct.sum()) == head["reported_direct_deaths"]
    assert np.isclose(tables["monthly_trend"].property_damage_usd.sum(), head["reported_property_damage_usd"])
    assert tables["state_comparison"].events.sum() == n
    ranked = events.sort_values(["property_damage_usd", "event_id"], ascending=[False, True])
    n_top = math.ceil(n * .01)
    top_share = ranked.head(n_top).property_damage_usd.sum() / ranked.property_damage_usd.sum() * 100
    assert np.isclose(top_share, tables["loss_concentration"].iloc[0].loss_share_pct)
    curve = ranked[["event_id", "property_damage_usd"]].copy()
    curve["event_rank"] = np.arange(1, n + 1)
    curve["cumulative_event_pct"] = curve.event_rank / n * 100
    curve["cumulative_loss_pct"] = curve.property_damage_usd.cumsum() / curve.property_damage_usd.sum() * 100
    curve.to_csv(EXPORTS / "loss_concentration_curve.csv", index=False)
    # Quantiles explicitly state the denominator and population.
    quantiles = []
    for name, frame in [("Full population", events), ("Routine comparison population", routine)]:
        for metric in ["duration_hours", "property_damage_usd"]:
            s = frame[metric].dropna()
            quantiles.append({"population": name, "metric": metric, "n": len(s), "mean": s.mean(),
                              "median": s.median(), "p90": s.quantile(.9), "p95": s.quantile(.95), "p99": s.quantile(.99), "max": s.max()})
    pd.DataFrame(quantiles).to_csv(EXPORTS / "distribution_summary.csv", index=False)
    outliers = events.loc[events.duration_outlier.eq(1) | events.damage_outlier.eq(1)]
    outliers[["event_id", "state", "cz_name", "duration_hours", "property_damage_usd", "duration_outlier", "damage_outlier", "source_file", "source_row"]].to_csv(EXPORTS / "routine_exclusions.csv", index=False)
    events.nlargest(20, "property_damage_usd")[["event_id", "episode_id", "state", "cz_name", "begin_at", "property_damage_usd", "deaths_direct", "event_narrative", "source_file", "source_row"]].to_csv(EXPORTS / "largest_loss_events.csv", index=False)
    events[events.duration_hours.gt(72)][["event_id", "state", "begin_at", "end_at", "duration_hours", "event_narrative"]].to_csv(EXPORTS / "long_duration_review.csv", index=False)
    direct = fatalities[fatalities.fatality_type.eq("D")]
    known_context = direct[~direct.fatality_location.isin(["Unknown", "Other"])]
    overnight = tables["overnight_start"].set_index("start_period")
    casualty = events.deaths_direct.add(events.injuries_direct).gt(0)
    reconciliation = tables["fatality_reconciliation"]
    gini_values = np.sort(events.property_damage_usd.fillna(0).to_numpy())
    loss_gini = float((2 * np.arange(1, n + 1) - n - 1) @ gini_values / (n * gini_values.sum()))
    episode_share = tables["episode_impacts"].head(math.ceil(len(tables["episode_impacts"]) * .01)).property_damage_usd.sum() / events.property_damage_usd.sum() * 100
    summary = dict(head)
    summary.update({
        "median_duration_hours": events.duration_hours.median(), "p90_duration_hours": events.duration_hours.quantile(.9),
        "median_positive_property_damage_usd": events.loc[events.property_damage_usd.gt(0), "property_damage_usd"].median(),
        "top_1pct_event_count": n_top, "top_1pct_loss_share_pct": top_share,
        "top_1pct_episode_loss_share_pct": episode_share, "property_loss_gini": loss_gini,
        "zero_property_damage_pct": events.property_damage_status.eq("zero").mean() * 100,
        "positive_property_damage_pct": events.property_damage_status.eq("positive").mean() * 100,
        "property_field_completion_pct": events.property_damage_status.isin(["zero", "positive"]).mean() * 100,
        "event_location_coverage_pct": events.valid_location_records.gt(0).mean() * 100,
        "event_narrative_completion_pct": events.event_narrative.notna().mean() * 100,
        "direct_casualty_events": int(casualty.sum()),
        "zero_damage_direct_casualty_events": int((casualty & events.property_damage_status.eq("zero")).sum()),
        "zero_damage_among_direct_casualty_events_pct": events.loc[casualty, "property_damage_status"].eq("zero").mean() * 100,
        "overnight_event_share_pct": events.is_overnight_start.mean() * 100,
        "overnight_direct_death_share_pct": overnight.loc["Overnight start", "direct_deaths"] / events.deaths_direct.sum() * 100,
        "overnight_fatal_event_ratio": overnight.loc["Overnight start", "fatal_event_pct"] / overnight.loc["Other start", "fatal_event_pct"],
        "direct_fatality_records": len(direct), "all_fatality_records": len(fatalities),
        "vehicle_direct_records": int(direct.fatality_location.eq("Vehicle/Towed Trailer").sum()),
        "vehicle_share_all_direct_records_pct": direct.fatality_location.eq("Vehicle/Towed Trailer").mean() * 100,
        "vehicle_share_known_location_direct_records_pct": known_context.fatality_location.eq("Vehicle/Towed Trailer").mean() * 100,
        "known_fatality_location_pct": len(known_context) / len(direct) * 100,
        "fatality_reconciliation_events": len(reconciliation),
        "direct_record_minus_summary_deaths": int(direct.shape[0] - events.deaths_direct.sum()),
        "duration_outliers": int(events.duration_outlier.sum()), "damage_outliers": int(events.damage_outlier.sum()),
        "routine_excluded_events": n - len(routine), "routine_events": len(routine),
        "routine_excluded_event_pct": (n - len(routine)) / n * 100,
        "routine_retained_loss_pct": routine.property_damage_usd.sum() / events.property_damage_usd.sum() * 100,
        "routine_removed_loss_pct": (1 - routine.property_damage_usd.sum() / events.property_damage_usd.sum()) * 100,
        "zero_duration_events": int(events.duration_hours.eq(0).sum()),
        "long_duration_review_events": int(events.duration_hours.gt(72).sum()),
        "naive_join_rows": int(naive.joined_rows), "naive_join_damage_usd": naive.joined_damage_usd,
        "naive_join_damage_inflation_factor": naive.joined_damage_usd / events.property_damage_usd.sum(),
        "raw_source_tables": 3, "raw_source_files": 15,
        "study_start": "2020-01-01", "study_end": "2024-12-31", "scope": "50 U.S. states and Washington, D.C.",
        "validation": "SQL/pandas event counts, damage, deaths, monthly totals, state totals, and top-1% concentration reconciled",
    })
    (EXPORTS / "kpi_summary.json").write_text(json.dumps(clean_json(summary), indent=2, allow_nan=False) + "\n")
    print(json.dumps(clean_json(summary), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
