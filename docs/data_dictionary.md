# Analytical model dictionary

The raw extracts retain all source fields. This dictionary covers the typed SQLite model. Provenance rows refer to committed extracts, not the larger all-hazard downloads.

## dim_date

One calendar date; 1,827 rows. The spine includes every day of the five-year study.

| Column | SQLite type | Key / requirement | Definition |
|---|---|---|---|

| `date_key` | INTEGER | Primary key | YYYYMMDD key from parsed event begin time; nullable only if the timestamp cannot be parsed. |

| `calendar_date` | TEXT | Required | Calendar spine date in YYYY-MM-DD format. |

| `year` | INTEGER | Required | Source study year (event table) or calendar year (date dimension). |

| `month` | INTEGER | Required | Parsed begin month or calendar month, 1–12. |

| `month_name` | TEXT | Required | Full English calendar month name. |

| `quarter` | INTEGER | Required | Calendar quarter, 1–4. |

| `day_of_week` | TEXT | Required | Full English weekday name from the calendar spine. |

| `is_weekend` | INTEGER | Required | 1 for Saturday/Sunday in the calendar spine; otherwise 0. |

## dim_geography

One observed state + county/equivalent key; 2,383 rows.

| Column | SQLite type | Key / requirement | Definition |
|---|---|---|---|

| `geography_key` | TEXT | Primary key | State FIPS padded to 2 digits + source CZ_TYPE + county/zone FIPS padded to 3 digits; e.g. 01C001. |

| `state_fips` | INTEGER | Required | Numeric state FIPS from the details source; scope uses an explicit list of 50 states plus D.C. |

| `state` | TEXT | Required | Source state name, in uppercase. |

| `cz_type` | TEXT | Required | Source county/zone/marine designator; all in-scope Flash Flood records are C. |

| `cz_fips` | INTEGER | Required | Source county or equivalent code; meaningful together with state and CZ_TYPE. |

| `cz_name` | TEXT | Required | Source county/equivalent label; latest observed label is chosen deterministically per geography key. |

## dim_episode

One NOAA episode ID represented in the selected flash-flood population; 5,162 rows.

| Column | SQLite type | Key / requirement | Definition |
|---|---|---|---|

| `episode_id` | INTEGER | Primary key | NOAA reporting-group ID; only represented flash-flood records are summarized here. |

| `first_event_at` | TEXT | Nullable | Earliest in-scope flash-flood begin time represented in the episode; reported local time. |

| `last_event_at` | TEXT | Nullable | Latest in-scope flash-flood end time represented in the episode; reported local time. |

| `event_count` | INTEGER | Required | Number of in-scope flash-flood event IDs in the episode. |

## fact_event

One in-scope NOAA event ID; 19,191 rows. All headline impact sums use this grain.

| Column | SQLite type | Key / requirement | Definition |
|---|---|---|---|

| `event_id` | INTEGER | Primary key | NOAA event ID; event-table primary key and child-table foreign key. In the audit, retained as source text. |

| `episode_id` | INTEGER | Required | NOAA reporting-group ID; only represented flash-flood records are summarized here. |

| `geography_key` | TEXT | Required | State FIPS padded to 2 digits + source CZ_TYPE + county/zone FIPS padded to 3 digits; e.g. 01C001. |

| `date_key` | INTEGER | Nullable | YYYYMMDD key from parsed event begin time; nullable only if the timestamp cannot be parsed. |

| `year` | INTEGER | Required | Source study year (event table) or calendar year (date dimension). |

| `month` | INTEGER | Nullable | Parsed begin month or calendar month, 1–12. |

| `begin_hour` | INTEGER | Nullable | Parsed event start hour, 0–23, in source-reported local time. |

| `begin_at` | TEXT | Nullable | Parsed BEGIN_DATE_TIME, stored as YYYY-MM-DD HH:MM:SS without cross-zone conversion. |

| `end_at` | TEXT | Nullable | Parsed END_DATE_TIME, stored as YYYY-MM-DD HH:MM:SS without cross-zone conversion. |

| `reported_timezone` | TEXT | Nullable | Original CZ_TIMEZONE label; timestamps are not converted to UTC. |

| `duration_hours` | REAL | Nullable | Nonnegative (end_at - begin_at) in hours; negative or unparseable intervals become null. |

| `is_overnight_start` | INTEGER | Nullable | 1 if begin hour is 20–23 or 0–5, else 0; null if hour is unknown. |

| `property_damage_raw` | TEXT | Nullable | Original DAMAGE_PROPERTY token, e.g. 10.00K; preserved alongside dollars. |

| `property_damage_usd` | REAL | Nullable | Parsed nominal dollars; H/K/M/B suffixes map to 100/1,000/1,000,000/1,000,000,000. |

| `property_damage_status` | TEXT | Required | One of positive, zero, missing, or invalid; unknown values are never silently zero-filled. |

| `crop_damage_raw` | TEXT | Nullable | Original DAMAGE_CROPS token, preserved alongside parsed dollars. |

| `crop_damage_usd` | REAL | Nullable | Parsed nominal crop-damage dollars using the same suffix mapping. |

| `crop_damage_status` | TEXT | Required | One of positive, zero, missing, or invalid. |

| `deaths_direct` | INTEGER | Nullable | Source event-summary DEATHS_DIRECT; nonnegative integer. Supplies headline direct deaths. |

| `deaths_indirect` | INTEGER | Nullable | Source event-summary DEATHS_INDIRECT; maintained separately from direct deaths. |

| `injuries_direct` | INTEGER | Nullable | Source event-summary INJURIES_DIRECT; nonnegative integer. |

| `injuries_indirect` | INTEGER | Nullable | Source event-summary INJURIES_INDIRECT; maintained separately from direct injuries. |

| `source` | TEXT | Nullable | Reported observation-source category, e.g. law enforcement or emergency manager; not the publisher. |

| `flood_cause` | TEXT | Nullable | Source-reported cause label; presence is not an independently validated causal estimate. |

| `event_narrative` | TEXT | Nullable | Source event narrative with surrounding whitespace stripped; blank stays missing. |

| `duration_outlier` | INTEGER | Required | 1 if duration is above the full-study upper 1.5×IQR fence; otherwise 0. |

| `damage_outlier` | INTEGER | Required | 1 if property damage exceeds the inverse-transformed upper fence of log(1 + positive loss). |

| `source_file` | TEXT | Required | Name of the committed filtered extract. The lock file links it to the original full NOAA snapshot. |

| `source_row` | INTEGER | Required | 1-based row number in the committed extract including its header; first data record is row 2. Not the all-hazard source-export row number. |

## fact_location

One event ID + location index; 58,578 rows. An event can have zero or many points.

| Column | SQLite type | Key / requirement | Definition |
|---|---|---|---|

| `event_id` | INTEGER | Primary key | NOAA event ID; event-table primary key and child-table foreign key. In the audit, retained as source text. |

| `location_index` | INTEGER | Primary key | NOAA point index within an event; composite primary key with event_id. |

| `location` | TEXT | Nullable | Source reference settlement/location label; not a postal address or geocoded footprint. |

| `latitude` | REAL | Nullable | Numeric source latitude; out-of-range or unparseable values become null. |

| `longitude` | REAL | Nullable | Numeric source longitude; out-of-range or unparseable values become null. |

| `latitude_raw` | TEXT | Nullable | Original source latitude cell string. |

| `longitude_raw` | TEXT | Nullable | Original source longitude cell string. |

| `coordinate_valid` | INTEGER | Required | 1 for a numeric in-range latitude/longitude pair other than (0,0); no state-boundary validation is claimed. |

| `source_file` | TEXT | Required | Name of the committed filtered extract. The lock file links it to the original full NOAA snapshot. |

| `source_row` | INTEGER | Required | 1-based row number in the committed extract including its header; first data record is row 2. Not the all-hazard source-export row number. |

## fact_fatality

One NOAA fatality ID; 401 rows. Includes 391 direct and 10 indirect records.

| Column | SQLite type | Key / requirement | Definition |
|---|---|---|---|

| `fatality_id` | INTEGER | Primary key | NOAA identifier for an individual fatality child record; primary key. |

| `event_id` | INTEGER | Required | NOAA event ID; event-table primary key and child-table foreign key. In the audit, retained as source text. |

| `fatality_type` | TEXT | Nullable | D = source-classified direct; I = indirect. Unrecognized types stay unclassified and are flagged. |

| `age_years` | INTEGER | Nullable | Numeric source age; negative, fractional, or above-120 values are nulled; missing remains unknown. |

| `fatality_sex` | TEXT | Nullable | Source sex classification; blank values map to Unknown. |

| `fatality_location` | TEXT | Nullable | Source context label; legacy codes are normalized where explicitly mapped. Unknown and Other remain distinct labels. |

| `source_file` | TEXT | Required | Name of the committed filtered extract. The lock file links it to the original full NOAA snapshot. |

| `source_row` | INTEGER | Required | 1-based row number in the committed extract including its header; first data record is row 2. Not the all-hazard source-export row number. |

## data_issue

One source field / analytical rule / source-row flag. An event can have multiple issues; scope flags include records outside the final fact table.

| Column | SQLite type | Key / requirement | Definition |
|---|---|---|---|

| `issue_id` | TEXT | Primary key | Deterministic truncated SHA-256 of table, extract, row, rule, and column; audit primary key. |

| `table_name` | TEXT | Required | Affected source-domain table: event, location, or fatality. |

| `event_id` | TEXT | Nullable | NOAA event ID; event-table primary key and child-table foreign key. In the audit, retained as source text. |

| `source_file` | TEXT | Nullable | Name of the committed filtered extract. The lock file links it to the original full NOAA snapshot. |

| `source_row` | INTEGER | Nullable | 1-based row number in the committed extract including its header; first data record is row 2. Not the all-hazard source-export row number. |

| `rule` | TEXT | Required | Machine-readable scope, validation, missingness, reconciliation, or statistical-tail rule. |

| `column_name` | TEXT | Nullable | Affected source or derived field. |

| `raw_value` | TEXT | Nullable | Source value or flagged derived value preserved for review. |

| `action` | TEXT | Required | Action actually applied, such as retaining both sources or excluding only from the routine view. |

| `severity` | TEXT | Required | scope, review, missing, statistical, invalid, or excluded; not every flag is a source error. |

## Views

`vw_event_enriched` adds county/state labels and pre-aggregated child counts while retaining one row per event. Its added metrics are `location_records`, `valid_location_records`, `fatality_records`, `direct_fatality_records`, and `indirect_fatality_records`. Missing child groups produce zero counts, not duplicate event rows.

`vw_routine_event` selects enriched events with both outlier flags equal to zero and a known duration. It does not alter `fact_event` or headline totals.
