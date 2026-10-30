"""Build the executed notebook and model dictionary from verified artifacts.

This utility uses the standard library to serialize notebook v4 JSON; each
Python code cell is actually executed, and its stdout becomes its saved output.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import sqlite3
import uuid

ROOT = Path(__file__).resolve().parents[1]


def notebook():
    cells, namespace, count = [], {}, 0

    def md(text):
        cells.append({"cell_type": "markdown", "id": uuid.uuid5(uuid.NAMESPACE_URL, text).hex[:8], "metadata": {}, "source": text.splitlines(True)})

    def code(text):
        nonlocal count
        count += 1
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exec(compile(text, f"notebook_cell_{count}", "exec"), namespace)
        outputs = [{"name": "stdout", "output_type": "stream", "text": out.getvalue().splitlines(True)}] if out.getvalue() else []
        cells.append({"cell_type": "code", "id": uuid.uuid5(uuid.NAMESPACE_URL, text).hex[:8], "metadata": {},
                      "execution_count": count, "source": text.splitlines(True), "outputs": outputs})

    md("# Flash-flood impacts: where the losses concentrate\n\nNOAA NCEI / NWS · 2020–2024 · 50 states and Washington, D.C.\n\nThis notebook reviews the built analytical model. Cleaning and model construction are implemented once in `src/floodfolio/`; run `python run_pipeline.py` before executing the notebook. All saved code outputs were executed against the frozen source snapshot.\n\nThe business question is where an operations review should start when recorded event volume, financial impact, and human impact produce different priorities.")
    code("from pathlib import Path\nimport sqlite3\nimport pandas as pd\n\nROOT = Path.cwd()\nif ROOT.name == 'notebooks':\n    ROOT = ROOT.parent\nconnection = sqlite3.connect(ROOT / 'data/processed/flash_flood.sqlite')\n\ndef query(filename):\n    return pd.read_sql_query((ROOT / 'sql' / filename).read_text(), connection)\n\nfor table in ['fact_event', 'fact_location', 'fact_fatality', 'dim_episode', 'dim_geography']:\n    count = connection.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]\n    print(f'{table:20s} {count:>8,}')\n")
    md("## 1. Reconcile the source grain before calculating impact\n\nLocations and fatalities are separate one-to-many tables. Counting unique event IDs after a direct join would not repair duplicated monetary sums.")
    code("correct = connection.execute('SELECT SUM(property_damage_usd) FROM fact_event').fetchone()[0]\nnaive = connection.execute('''\n    SELECT COUNT(*), SUM(e.property_damage_usd)\n    FROM fact_event e\n    LEFT JOIN fact_location l USING(event_id)\n    LEFT JOIN fact_fatality f USING(event_id)\n''').fetchone()\nprotected = connection.execute('SELECT COUNT(*), SUM(property_damage_usd) FROM vw_event_enriched').fetchone()\nprint(f'Protected event rows: {protected[0]:,}')\nprint(f'Protected damage: ${protected[1]:,.0f}')\nprint(f'Naive joined rows: {naive[0]:,}')\nprint(f'Naive joined damage: ${naive[1]:,.0f}')\nprint(f'Inflation factor: {naive[1] / correct:.4f}x')\nassert protected[1] == correct\n")
    md("## 2. Impact scorecard\n\nEvent-summary counts supply the casualty KPIs. Property and crop losses remain separate; all monetary values are nominal reported estimates.")
    code("headline = query('01_headline_kpis.sql')\nprint(headline.T.to_string(header=False))\n")
    md("## 3. Concentration, not the average event\n\nThe top-1% denominator is all event records, including explicit zero-loss entries. The selected count is rounded up, with event ID breaking ties deterministically.")
    code("print(query('04_loss_concentration.sql').to_string(index=False))\nevents = pd.read_sql_query('SELECT * FROM vw_event_enriched', connection)\npositive = events.loc[events.property_damage_usd > 0, 'property_damage_usd']\nprint(f'Positive-loss median: ${positive.median():,.0f}')\nprint(f'Positive-loss mean: ${positive.mean():,.0f}')\n")
    md("![Loss concentration](../reports/figures/02_loss_concentration.png)\n\nA default IQR filter on the untransformed, zero-heavy loss distribution would be a poor choice. The sensitivity analysis below preserves the complete impact population.")
    md("## 4. Event frequency and financial impact\n\nThe monthly SQL uses a calendar spine so zero-event months cannot disappear. All 60 monthly observations are retained in the chart and exported table.")
    code("monthly = query('02_monthly_trend.sql')\nprint(monthly.groupby('year')[['events', 'property_damage_usd', 'direct_deaths']].sum().to_string())\nprint(f'Months in calendar spine: {len(monthly)}')\nprint(query('03_state_comparison.sql')[['state','events','property_damage_usd','direct_deaths']].head(8).to_string(index=False))\n")
    md("![Monthly impacts](../reports/figures/04_monthly_impacts.png)")
    md("## 5. Overnight-start profile\n\nOvernight means 20:00–05:59 in NOAA's reported local time. It describes event start, not the time of death. The comparison is unadjusted and descriptive.")
    code("overnight = query('05_overnight_start.sql')\nprint(overnight.to_string(index=False))\nratio = overnight.set_index('start_period').fatal_event_pct\nprint(f'Unadjusted fatal-event proportion ratio: {ratio[\"Overnight start\"] / ratio[\"Other start\"]:.3f}x')\n")
    md("![Overnight profile](../reports/figures/03_overnight_profile.png)")
    md("## 6. What the source tables disagree about\n\nThe mismatch is retained. The event-summary total of 389 direct deaths and the 391 direct-fatality child records answer different source-specific questions.")
    code("print(query('07_fatality_reconciliation.sql').to_string(index=False))\nprint(query('06_fatality_context.sql').to_string(index=False))\n")
    md("## 7. Reporting quality beside the impact totals\n\nA zero monetary entry is not a missing field. Child-location coverage uses distinct parent events, not point counts.")
    code("print(pd.read_csv(ROOT / 'reports/tables/quality_by_year.csv').to_string(index=False))\ncasualty = events.deaths_direct.add(events.injuries_direct).gt(0)\nzero = events.property_damage_status.eq('zero')\nprint(f'Direct-casualty events: {casualty.sum():,}')\nprint(f'Direct-casualty events with zero property-damage entry: {(casualty & zero).sum():,}')\nprint(f'Among casualty events: {100 * zero[casualty].mean():.2f}%')\n")
    md("![Reporting coverage](../reports/figures/05_reporting_coverage.png)")
    md("## 8. Outlier removal changes the analytical question\n\nDuration flags use an upper 1.5×IQR fence. Property-loss flags apply that fence to log(1 + positive loss). The full population supplies headline impacts; the routine population excludes flags for comparison only.")
    code("print(query('09_outlier_sensitivity.sql').to_string(index=False))\nprint(events[['duration_hours', 'property_damage_usd']].quantile([.5, .9, .95, .99]).to_string())\nprint('Long-duration records awaiting source review:', int(events.duration_hours.gt(72).sum()))\nconnection.close()\n")
    md("![Outlier sensitivity](../reports/figures/06_outlier_sensitivity.png)\n\n## Implications\n\nSeparate high-impact episode review from routine event activity. Add reporting diagnostics to both. Investigate the overnight association only after adding severity, geography, and exposure information. Resolve the casualty-table discrepancy through source review.\n\nThe evidence does not establish causal effects, population-normalized risk, insurance losses, warning effectiveness, or a measured operational improvement. See the decision memo and limitations document for the proposed next stage.")
    target = ROOT / "notebooks/01_flash_flood_analysis.ipynb"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps({"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                                              "language_info": {"name": "python", "version": "3.12"}},
                                  "nbformat": 4, "nbformat_minor": 5}, indent=1) + "\n")
    print(f"Executed notebook: {count} code cells; {len(cells)} total cells")


def dictionary():
    descriptions = {
        "date_key": "YYYYMMDD key from parsed event begin time; nullable only if the timestamp cannot be parsed.",
        "calendar_date": "Calendar spine date in YYYY-MM-DD format.",
        "year": "Source study year (event table) or calendar year (date dimension).",
        "month": "Parsed begin month or calendar month, 1–12.",
        "month_name": "Full English calendar month name.",
        "quarter": "Calendar quarter, 1–4.",
        "day_of_week": "Full English weekday name from the calendar spine.",
        "is_weekend": "1 for Saturday/Sunday in the calendar spine; otherwise 0.",
        "geography_key": "State FIPS padded to 2 digits + source CZ_TYPE + county/zone FIPS padded to 3 digits; e.g. 01C001.",
        "state_fips": "Numeric state FIPS from the details source; scope uses an explicit list of 50 states plus D.C.",
        "state": "Source state name, in uppercase.",
        "cz_type": "Source county/zone/marine designator; all in-scope Flash Flood records are C.",
        "cz_fips": "Source county or equivalent code; meaningful together with state and CZ_TYPE.",
        "cz_name": "Source county/equivalent label; latest observed label is chosen deterministically per geography key.",
        "episode_id": "NOAA reporting-group ID; only represented flash-flood records are summarized here.",
        "first_event_at": "Earliest in-scope flash-flood begin time represented in the episode; reported local time.",
        "last_event_at": "Latest in-scope flash-flood end time represented in the episode; reported local time.",
        "event_count": "Number of in-scope flash-flood event IDs in the episode.",
        "event_id": "NOAA event ID; event-table primary key and child-table foreign key. In the audit, retained as source text.",
        "begin_hour": "Parsed event start hour, 0–23, in source-reported local time.",
        "begin_at": "Parsed BEGIN_DATE_TIME, stored as YYYY-MM-DD HH:MM:SS without cross-zone conversion.",
        "end_at": "Parsed END_DATE_TIME, stored as YYYY-MM-DD HH:MM:SS without cross-zone conversion.",
        "reported_timezone": "Original CZ_TIMEZONE label; timestamps are not converted to UTC.",
        "duration_hours": "Nonnegative (end_at - begin_at) in hours; negative or unparseable intervals become null.",
        "is_overnight_start": "1 if begin hour is 20–23 or 0–5, else 0; null if hour is unknown.",
        "property_damage_raw": "Original DAMAGE_PROPERTY token, e.g. 10.00K; preserved alongside dollars.",
        "property_damage_usd": "Parsed nominal dollars; H/K/M/B suffixes map to 100/1,000/1,000,000/1,000,000,000.",
        "property_damage_status": "One of positive, zero, missing, or invalid; unknown values are never silently zero-filled.",
        "crop_damage_raw": "Original DAMAGE_CROPS token, preserved alongside parsed dollars.",
        "crop_damage_usd": "Parsed nominal crop-damage dollars using the same suffix mapping.",
        "crop_damage_status": "One of positive, zero, missing, or invalid.",
        "deaths_direct": "Source event-summary DEATHS_DIRECT; nonnegative integer. Supplies headline direct deaths.",
        "deaths_indirect": "Source event-summary DEATHS_INDIRECT; maintained separately from direct deaths.",
        "injuries_direct": "Source event-summary INJURIES_DIRECT; nonnegative integer.",
        "injuries_indirect": "Source event-summary INJURIES_INDIRECT; maintained separately from direct injuries.",
        "source": "Reported observation-source category, e.g. law enforcement or emergency manager; not the publisher.",
        "flood_cause": "Source-reported cause label; presence is not an independently validated causal estimate.",
        "event_narrative": "Source event narrative with surrounding whitespace stripped; blank stays missing.",
        "duration_outlier": "1 if duration is above the full-study upper 1.5×IQR fence; otherwise 0.",
        "damage_outlier": "1 if property damage exceeds the inverse-transformed upper fence of log(1 + positive loss).",
        "source_file": "Name of the committed filtered extract. The lock file links it to the original full NOAA snapshot.",
        "source_row": "1-based row number in the committed extract including its header; first data record is row 2. Not the all-hazard source-export row number.",
        "location_index": "NOAA point index within an event; composite primary key with event_id.",
        "location": "Source reference settlement/location label; not a postal address or geocoded footprint.",
        "latitude": "Numeric source latitude; out-of-range or unparseable values become null.",
        "longitude": "Numeric source longitude; out-of-range or unparseable values become null.",
        "latitude_raw": "Original source latitude cell string.",
        "longitude_raw": "Original source longitude cell string.",
        "coordinate_valid": "1 for a numeric in-range latitude/longitude pair other than (0,0); no state-boundary validation is claimed.",
        "fatality_id": "NOAA identifier for an individual fatality child record; primary key.",
        "fatality_type": "D = source-classified direct; I = indirect. Unrecognized types stay unclassified and are flagged.",
        "age_years": "Numeric source age; negative, fractional, or above-120 values are nulled; missing remains unknown.",
        "fatality_sex": "Source sex classification; blank values map to Unknown.",
        "fatality_location": "Source context label; legacy codes are normalized where explicitly mapped. Unknown and Other remain distinct labels.",
        "issue_id": "Deterministic truncated SHA-256 of table, extract, row, rule, and column; audit primary key.",
        "table_name": "Affected source-domain table: event, location, or fatality.",
        "rule": "Machine-readable scope, validation, missingness, reconciliation, or statistical-tail rule.",
        "column_name": "Affected source or derived field.",
        "raw_value": "Source value or flagged derived value preserved for review.",
        "action": "Action actually applied, such as retaining both sources or excluding only from the routine view.",
        "severity": "scope, review, missing, statistical, invalid, or excluded; not every flag is a source error.",
    }
    table_notes = {
        "dim_date": "One calendar date; 1,827 rows. The spine includes every day of the five-year study.",
        "dim_geography": "One observed state + county/equivalent key; 2,383 rows.",
        "dim_episode": "One NOAA episode ID represented in the selected flash-flood population; 5,162 rows.",
        "fact_event": "One in-scope NOAA event ID; 19,191 rows. All headline impact sums use this grain.",
        "fact_location": "One event ID + location index; 58,578 rows. An event can have zero or many points.",
        "fact_fatality": "One NOAA fatality ID; 401 rows. Includes 391 direct and 10 indirect records.",
        "data_issue": "One source field / analytical rule / source-row flag. An event can have multiple issues; scope flags include records outside the final fact table.",
    }
    chunks=["# Analytical model dictionary\n", "The raw extracts retain all source fields. This dictionary covers the typed SQLite model. Provenance rows refer to committed extracts, not the larger all-hazard downloads.\n"]
    with sqlite3.connect(ROOT/"data/processed/flash_flood.sqlite") as connection:
        for table,note in table_notes.items():
            chunks += [f"## {table}\n",note+"\n", "| Column | SQLite type | Key / requirement | Definition |\n|---|---|---|---|\n"]
            for _,name,dtype,required,default,pk in connection.execute(f"PRAGMA table_info({table})"):
                requirement="Primary key" if pk else "Required" if required else "Nullable"
                definition=descriptions.get(name)
                if definition is None: raise ValueError(f"Undocumented model field: {table}.{name}")
                chunks.append(f"| `{name}` | {dtype} | {requirement} | {definition} |\n")
    chunks += ["## Views\n", "`vw_event_enriched` adds county/state labels and pre-aggregated child counts while retaining one row per event. Its added metrics are `location_records`, `valid_location_records`, `fatality_records`, `direct_fatality_records`, and `indirect_fatality_records`. Missing child groups produce zero counts, not duplicate event rows.\n", "`vw_routine_event` selects enriched events with both outlier flags equal to zero and a known duration. It does not alter `fact_event` or headline totals.\n"]
    (ROOT/"docs/data_dictionary.md").write_text("\n".join(chunks))
    print("Model dictionary: every typed column documented")


if __name__ == "__main__":
    os.chdir(ROOT)
    notebook()
    dictionary()
