# Data quality and analytical decisions

## A record is removed only for a stated reason

The raw layer preserves original source cell strings. The typed layer records provenance (`source_file`, `source_row`), and the `data_issue` table records each flagged source field and the action taken. The audit includes scope and statistical flags; it is not a count of proven source errors.

| Rule / observation | Snapshot result | Treatment |
|---|---:|---|
| Territory events outside the study geography | 558 events | Exclude from the model; retain raw rows |
| Linked child records outside the selected parent population | 1,724 rows | Exclude alongside their parents; 1,717 location and 7 fatality records |
| Exact duplicate business rows | 0 | If present, keep the first identical payload and log the repeated source row |
| Conflicting primary-key payloads | 0 | If present, quarantine all versions; do not select an arbitrary winner |
| Invalid required keys | 0 | Quarantine the affected row |
| Malformed or negative damage tokens | 0 | If present, preserve the token and set only the derived amount to null |
| Missing property/crop damage fields | 0 | Preserve as missing if present; never fill with zero |
| Invalid or negative casualty counts | 0 | If present, null the count and log the source value |
| Invalid coordinate ranges | 0 | If present, null the coordinate and exclude the point from spatial summaries |
| Zero recorded duration | 1,269 events | Retain as recorded; timing precision and source conventions are unresolved |
| Recorded duration above 72 hours | 9 events | Queue for source review; retain all impact values |
| Missing event narrative | 43 events | Preserve missingness; do not generate descriptions |
| Duration statistical tail | 1,086 events | Flag in the full table; exclude only from the routine comparison |
| Damage statistical tail | 160 events | Same; preserve the full recorded losses |
| Cross-table casualty mismatch | 1 event, +2 direct child records | Retain both sources; use event-summary counts for headline KPIs |

## The casualty discrepancy

**Event 970467**, Tuscaloosa County, Alabama, in the 2021 source file:

| Source | Direct-death count |
|---|---:|
| Event summary, `DEATHS_DIRECT` | 0 |
| Linked fatality records classified direct | 2 |

The project does not establish which version is correct. Headline event-summary totals are **389 direct deaths**; the direct-fatality context analysis contains **391 direct records**. The 10 indirect deaths reconcile. The discrepancy is exported in `reports/tables/fatality_reconciliation.csv` and recorded in the audit table. A contract test ensures that it remains visible.

## Why extreme losses were retained

The five largest entries each report $500M, with narratives describing major regional impacts. Repeated round monetary amounts are not sufficient evidence of duplicate events or data entry mistakes. The events have distinct IDs, places, and dates. The project keeps those source estimates and makes their concentration explicit.

The duration tail is different: the largest interval is **608.25 hours**, while its narrative describes impacts over hours. That is a reason to investigate the timestamps, not enough evidence to invent a corrected end date. Nine intervals exceed 72 hours. They are listed in `reports/tables/long_duration_review.csv` and excluded by the stricter routine-duration fence.

## Why zero is not missing—and not certainty

There are **13,478 explicit zero property-damage entries**. All property-damage fields parse successfully, so this snapshot has 100% field completion. Nevertheless, a zero field does not independently verify the absence of loss. The data does not provide an additional flag separating assessed-zero damage from an unquantified estimate.

Among the 218 events with a reported direct death or injury, 101 have a zero property-damage entry. That combination is possible: human impact does not require property damage. It is a useful reporting diagnostic, not proof that the damage entry is wrong.

## Spatial coverage requires a denominator

The 58,578 child location records correspond to **13,483 distinct events**, or 70.3% of the event population. Counting location rows would overstate spatial coverage. Missing child records do not imply that the separate begin/end coordinates in event details are absent.

Coverage is calculated separately for each year. The linked-location proportion decreases from 98.0% in 2020 to 57.0% in 2024. The pipeline does not infer why. Any geographic extension should profile both coordinate sources, missingness by reporting office, and the selection effects of choosing one source over another.

## Source updates are controlled

Source file creation dates and hashes are locked. A default build reads committed extracts without a network request. `scripts/download_data.py` verifies full-source downloads against the lock before recreating the extracts. A changed source fails verification. An intentional `--refresh-lock` is a new analytical snapshot and requires reviewing row counts, discrepancies, and findings.

## Audit outputs

- `cleaning_waterfall.csv`: every scope, duplicate, conflict, and key-validation step, including steps that remove zero rows.
- `data_issues.csv`: row-level flags and actions. Multiple flags can refer to the same event.
- `routine_exclusions.csv`: distinct events removed from the comparison population, with flags and source lineage.
- `fatality_reconciliation.csv`: event-summary versus fatality-child count differences.
- `largest_loss_events.csv`: source narratives for the 20 largest reported property losses.
- `long_duration_review.csv`: intervals above 72 hours, preserving source narratives.
- `pipeline_summary.json`: table sizes, rule counts, and calculated outlier thresholds.
