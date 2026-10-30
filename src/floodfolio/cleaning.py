"""Typed cleaning with field-level audit trails and preserved source values."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import hashlib
import re

import numpy as np
import pandas as pd

from .config import RAW, STATE_FIPS, OVERNIGHT_HOURS


def parse_damage(value) -> tuple[float | None, str]:
    """Return dollars and status; missing/invalid entries never become zero."""
    if value is None or pd.isna(value) or str(value).strip().lower() in {"", "null", "nan", "na"}:
        return None, "missing"
    text = str(value).strip().upper()
    match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*([HKMB]?)", text)
    if not match:
        return None, "invalid"
    factors = {"": 1, "H": 100, "K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
    try:
        dollars = float(Decimal(match[1]) * factors[match[2]])
    except (InvalidOperation, OverflowError):
        return None, "invalid"
    if not np.isfinite(dollars):
        return None, "invalid"
    return dollars, "zero" if dollars == 0 else "positive"


def iqr_upper(values: pd.Series) -> float:
    valid = values.dropna()
    if valid.empty:
        return float("inf")
    q1, q3 = valid.quantile([0.25, 0.75])
    return float(q3 + 1.5 * (q3 - q1))


def read_raw(table: str) -> pd.DataFrame:
    frames = []
    for path in sorted(RAW.glob(f"{table}_*.csv.gz")):
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        frame.columns = frame.columns.str.lower()
        frame["source_file"] = path.name
        frame["source_row"] = np.arange(2, len(frame) + 2)
        frames.append(frame)
    if not frames:
        raise FileNotFoundError(f"No {table} extracts in {RAW}; run scripts/download_data.py")
    return pd.concat(frames, ignore_index=True)


class Audit:
    def __init__(self):
        self.issues: list[dict] = []
        self.steps: list[dict] = []

    def add(self, frame: pd.DataFrame, mask: pd.Series, table: str, rule: str,
            column: str, action: str, severity: str = "review") -> None:
        for _, row in frame.loc[mask].iterrows():
            identity = f"{table}|{row['source_file']}|{row['source_row']}|{rule}|{column}"
            self.issues.append({
                "issue_id": hashlib.sha256(identity.encode()).hexdigest()[:20],
                "table_name": table, "event_id": row.get("event_id", ""),
                "source_file": row["source_file"], "source_row": int(row["source_row"]),
                "rule": rule, "column_name": column,
                "raw_value": str(row.get(column, "")), "action": action, "severity": severity,
            })

    def step(self, table, rule, before, after):
        self.steps.append({"table_name": table, "rule": rule, "rows_before": int(before),
                           "rows_after": int(after), "rows_removed": int(before - after)})

    def dedupe(self, frame: pd.DataFrame, table: str, keys: list[str]) -> pd.DataFrame:
        # Provenance fields are not part of business-row equality.
        payload = [c for c in frame.columns if c not in {"source_file", "source_row"}]
        exact = frame.duplicated(payload, keep="first")
        self.add(frame, exact, table, "exact_duplicate", keys[0], "drop_duplicate", "excluded")
        result = frame.loc[~exact].copy()
        self.step(table, "exact_duplicate", len(frame), len(result))
        conflict = result.duplicated(keys, keep=False)
        self.add(result, conflict, table, "conflicting_primary_key", keys[0], "quarantine_all_conflicting_rows", "excluded")
        final = result.loc[~conflict].copy()
        self.step(table, "conflicting_primary_key", len(result), len(final))
        return final.reset_index(drop=True)


def clean_events(raw: pd.DataFrame, audit: Audit) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    d = raw.copy()
    scope = pd.to_numeric(d.state_fips, errors="coerce").isin(STATE_FIPS)
    audit.add(d, ~scope, "event", "outside_geographic_scope", "state", "exclude_from_study", "scope")
    audit.step("event", "geographic_scope", len(d), int(scope.sum()))
    d = audit.dedupe(d.loc[scope].copy(), "event", ["event_id"])
    for col in ["event_id", "episode_id", "state_fips", "cz_fips", "year"]:
        values = pd.to_numeric(d[col], errors="coerce")
        invalid = values.isna() | (values < 0) | (values % 1 != 0)
        audit.add(d, invalid, "event", "invalid_required_key", col, "quarantine_row", "excluded")
        before = len(d)
        d = d.loc[~invalid].copy()
        audit.step("event", f"valid_{col}", before, len(d))
        d[col] = pd.to_numeric(d[col]).astype("int64")
    d["begin_at"] = pd.to_datetime(d.begin_date_time, format="%d-%b-%y %H:%M:%S", errors="coerce")
    d["end_at"] = pd.to_datetime(d.end_date_time, format="%d-%b-%y %H:%M:%S", errors="coerce")
    for col, source in [("begin_at", "begin_date_time"), ("end_at", "end_date_time")]:
        audit.add(d, d[col].isna(), "event", "invalid_timestamp", source, "null_derived_time_fields", "invalid")
    d["duration_hours"] = (d.end_at - d.begin_at).dt.total_seconds() / 3600
    negative = d.duration_hours < 0
    audit.add(d, negative, "event", "negative_duration", "end_date_time", "null_duration_only", "invalid")
    d.loc[negative, "duration_hours"] = np.nan
    zero = d.duration_hours.eq(0)
    audit.add(d, zero, "event", "zero_duration", "begin_date_time", "retain_as_recorded", "review")
    audit.add(d, d.duration_hours.gt(72), "event", "extended_duration_review", "end_date_time", "retain_pending_source_review", "review")
    d["date_key"] = d.begin_at.dt.strftime("%Y%m%d").astype("Int64")
    d["month"] = d.begin_at.dt.month.astype("Int64")
    d["begin_hour"] = d.begin_at.dt.hour.astype("Int64")
    d["is_overnight_start"] = d.begin_hour.isin(OVERNIGHT_HOURS).astype(int)
    d.loc[d.begin_hour.isna(), "is_overnight_start"] = pd.NA
    d["geography_key"] = d.state_fips.map(lambda x: f"{x:02d}") + d.cz_type + d.cz_fips.map(lambda x: f"{x:03d}")
    for source, dest in [("damage_property", "property_damage"), ("damage_crops", "crop_damage")]:
        parsed = d[source].map(parse_damage)
        d[f"{dest}_usd"] = parsed.map(lambda x: x[0])
        d[f"{dest}_status"] = parsed.map(lambda x: x[1])
        audit.add(d, d[f"{dest}_status"].eq("invalid"), "event", "invalid_damage_token", source, "null_amount_retain_token", "invalid")
        audit.add(d, d[f"{dest}_status"].eq("missing"), "event", "missing_damage", source, "retain_missing", "missing")
    for col in ["deaths_direct", "deaths_indirect", "injuries_direct", "injuries_indirect"]:
        values = pd.to_numeric(d[col], errors="coerce")
        invalid = values.isna() | values.lt(0) | values.mod(1).ne(0)
        audit.add(d, invalid, "event", "invalid_casualty_count", col, "null_count", "invalid")
        d[col] = values.mask(invalid).astype("Int64")
    for col in ["event_narrative", "episode_narrative", "source", "flood_cause"]:
        missing = d[col].str.strip().eq("")
        audit.add(d, missing, "event", "missing_context", col, "retain_missing", "missing")
        d[col] = d[col].str.strip().replace("", pd.NA)
    # Statistical filtering is isolated to a routine-event view, never headline totals.
    duration_upper = iqr_upper(d.duration_hours)
    log_loss = np.log1p(d.loc[d.property_damage_usd.gt(0), "property_damage_usd"])
    damage_upper = float(np.expm1(iqr_upper(log_loss)))
    d["duration_outlier"] = d.duration_hours.gt(duration_upper).astype(int)
    d["damage_outlier"] = d.property_damage_usd.gt(damage_upper).astype(int)
    for column, flag in [("duration_hours", "duration_outlier"), ("damage_property", "damage_outlier")]:
        audit.add(d, d[flag].eq(1), "event", "statistical_outlier", column,
                  "retain_full_population_exclude_routine_view", "statistical")
    # Keep a stable reference row for names, and a source record for each fact.
    geographies = d.sort_values(["begin_at", "event_id"]).drop_duplicates("geography_key", keep="last")
    geographies = geographies[["geography_key", "state_fips", "state", "cz_type", "cz_fips", "cz_name"]].copy()
    episodes = d.groupby("episode_id", as_index=False).agg(
        first_event_at=("begin_at", "min"), last_event_at=("end_at", "max"),
        event_count=("event_id", "size"),
    )
    # An episode dimension summarizes only the in-scope flash-flood records.
    episodes["first_event_at"] = episodes.first_event_at.dt.strftime("%Y-%m-%d %H:%M:%S")
    episodes["last_event_at"] = episodes.last_event_at.dt.strftime("%Y-%m-%d %H:%M:%S")
    fields = ["event_id", "episode_id", "geography_key", "date_key", "year", "month", "begin_hour",
              "begin_at", "end_at", "cz_timezone", "duration_hours", "is_overnight_start",
              "damage_property", "property_damage_usd", "property_damage_status", "damage_crops",
              "crop_damage_usd", "crop_damage_status", "deaths_direct", "deaths_indirect",
              "injuries_direct", "injuries_indirect", "source", "flood_cause", "event_narrative",
              "duration_outlier", "damage_outlier", "source_file", "source_row"]
    result = d[fields].copy()
    for col in ["begin_at", "end_at"]:
        result[col] = result[col].dt.strftime("%Y-%m-%d %H:%M:%S")
    result = result.rename(columns={"cz_timezone": "reported_timezone", "damage_property": "property_damage_raw", "damage_crops": "crop_damage_raw"})
    return result, geographies, episodes, {"duration_upper_hours": duration_upper, "positive_log_damage_upper_usd": damage_upper}


def clean_children(raw: pd.DataFrame, kind: str, events: pd.DataFrame, audit: Audit) -> pd.DataFrame:
    d = raw.copy()
    ids = set(events.event_id.astype(str))
    matched = d.event_id.isin(ids)
    audit.add(d, ~matched, kind, "parent_outside_study", "event_id", "exclude_with_parent", "scope")
    audit.step(kind, "parent_in_scope", len(d), int(matched.sum()))
    d = d.loc[matched].copy()
    keys = ["event_id", "location_index"] if kind == "location" else ["fatality_id"]
    d = audit.dedupe(d, kind, keys)
    for col in dict.fromkeys(keys + ["event_id"]):
        values = pd.to_numeric(d[col], errors="coerce")
        invalid = values.isna() | values.lt(0) | values.mod(1).ne(0)
        audit.add(d, invalid, kind, "invalid_required_key", col, "quarantine_row", "excluded")
        before = len(d)
        d = d.loc[~invalid].copy()
        d[col] = pd.to_numeric(d[col]).astype("int64")
        audit.step(kind, f"valid_{col}", before, len(d))
    if kind == "location":
        for col, lower, upper in [("latitude", -90, 90), ("longitude", -180, 180)]:
            d[col + "_raw"] = d[col]
            values = pd.to_numeric(d[col], errors="coerce")
            invalid = ~values.between(lower, upper)
            audit.add(d, invalid, kind, "invalid_coordinate", col, "null_coordinate", "invalid")
            d[col] = values.mask(invalid)
        d["coordinate_valid"] = (d.latitude.notna() & d.longitude.notna() & ~(d.latitude.eq(0) & d.longitude.eq(0))).astype(int)
        audit.add(d, d.coordinate_valid.eq(0), kind, "unusable_coordinate_pair", "latitude_raw", "exclude_from_maps_only", "invalid")
        return d[["event_id", "location_index", "location", "latitude", "longitude", "latitude_raw", "longitude_raw", "coordinate_valid", "source_file", "source_row"]]
    ages = pd.to_numeric(d.fatality_age, errors="coerce")
    bad_age = ages.notna() & (~ages.between(0, 120) | ages.mod(1).ne(0))
    audit.add(d, bad_age, kind, "implausible_age", "fatality_age", "null_age_only", "invalid")
    d["age_years"] = ages.mask(bad_age).astype("Int64")
    d["fatality_location"] = d.fatality_location.str.strip().replace({"": "Unknown", "VE": "Vehicle/Towed Trailer", "IW": "In Water", "PH": "Permanent Home", "OU": "Outside/Open Areas", "OT": "Unknown"})
    d["fatality_sex"] = d.fatality_sex.str.strip().replace("", "Unknown")
    unknown_type = ~d.fatality_type.isin(["D", "I"])
    audit.add(d, unknown_type, kind, "unknown_fatality_type", "fatality_type", "retain_unclassified", "review")
    return d[["fatality_id", "event_id", "fatality_type", "age_years", "fatality_sex", "fatality_location", "source_file", "source_row"]]
