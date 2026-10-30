# Metric definitions

All impact KPIs use the full in-scope population unless a population is explicitly named. The scope is Flash Flood records in the 50 U.S. states and Washington, D.C., with source years 2020–2024. Values are produced by the committed SQL and `src/floodfolio/analysis.py`.

| Metric | Formula / denominator | Implementation | Interpretation boundary |
|---|---|---|---|
| Recorded events | `COUNT(*)` at unique event-ID grain | `01_headline_kpis.sql` | County-level records, not unique nationwide storms |
| Recorded episode IDs | `COUNT(DISTINCT episode_id)` | `01_headline_kpis.sql` | Only episodes represented by in-scope flash-flood records |
| Counties with records | Distinct `state_fips + cz_type + cz_fips` | `01_headline_kpis.sql` | Observed coverage, not all counties in the United States |
| Reported property damage | Sum of parsed `DAMAGE_PROPERTY` values | `01_headline_kpis.sql` | Nominal USD; broad recorded estimates; no inflation adjustment |
| Reported crop damage | Separate sum of parsed `DAMAGE_CROPS` | `01_headline_kpis.sql` | Not combined with property loss in concentration analysis |
| Reported direct / indirect deaths | Separate sums of event-summary fields | `01_headline_kpis.sql` | Child fatality record counts do not overwrite the event summary |
| Reported direct / indirect injuries | Separate sums of event-summary fields | `01_headline_kpis.sql` | Recorded counts; no assumptions about missing injuries |
| Fatal events | Events with `deaths_direct > 0` | `01_headline_kpis.sql` | Presence of at least one reported direct death |
| Median / P90 duration | Median / 90th percentile of nonnegative parsed `(end - start)` hours | `analysis.py` | Recorded interval, not warning lead time or response time |
| Mean / median positive loss | Mean / median of property-damage values strictly above zero | `01_headline_kpis.sql`, `analysis.py` | Denominator excludes explicit zero entries |
| Monthly year-over-year event change | `(events - LAG(events,12)) / LAG(events,12)`; calendar spine contains all 60 months | `02_monthly_trend.sql` | Descriptive change in reporting counts; first 12 months have no prior-year baseline |
| Top-1% event loss share | Sum of largest `ceil(0.01 × N)` event losses / all reported property loss | `04_loss_concentration.sql` | N includes zero entries; deterministic event-ID tiebreaker |
| Top-1% episode loss share | Largest `ceil(0.01 × number of episode IDs)` episode totals / all property loss | `10_episode_impacts.sql`, `analysis.py` | Episode IDs are administrative reporting groups |
| Property-loss Gini | Standard empirical Gini of all event-level property-damage entries | `analysis.py` | Exploratory concentration statistic; highly sensitive to explicit zeros |
| Overnight event share | Events beginning 20:00–05:59 / events with a known start hour | `analysis.py` | Based on reported local time, not calculated darkness |
| Overnight direct-death share | Direct deaths in overnight-start events / direct deaths in all classified events | `05_overnight_start.sql`, `analysis.py` | The event's start time does not establish the time of a death |
| Fatal-event proportion | Events with a direct death / all events in the start-period group | `05_overnight_start.sql` | Event-level proportion; does not use individual victims as the denominator |
| Overnight fatal-event ratio | Overnight fatal-event proportion / other-start fatal-event proportion | `05_overnight_start.sql`, `analysis.py` | Unadjusted descriptive association; no exposure or severity control |
| Direct deaths per 1,000 recorded events | Direct event-summary deaths / recorded events × 1,000 | `03_state_comparison.sql`, `05_overnight_start.sql` | Not a population mortality rate or a person-level risk estimate |
| Explicit zero-damage share | `property_damage_status = 'zero'` events / all events | `08_reporting_diagnostics.sql`, `analysis.py` | Cannot distinguish absence of damage from unquantified damage |
| Positive-damage share | Positive property-damage entries / all events | `03_state_comparison.sql`, `analysis.py` | Reporting characteristic, not the proportion of all floods causing damage |
| Damage-field completion | Valid numeric positive or zero property-damage entries / all events | `analysis.py` | 100% completion can coexist with ambiguous zero entries |
| Zero damage among direct-casualty events | Events with zero property damage and `deaths_direct + injuries_direct > 0` / all direct-casualty events | `08_reporting_diagnostics.sql`, `analysis.py` | Diagnostic cross-tabulation; human impact does not require property loss |
| Valid linked-location coverage | Events with at least one child point whose coordinates are numeric, in global ranges, and not the zero-zero pair / all events | `00_schema.sql`, `analysis.py` | Does not assess the details file's coordinates or geocode accuracy |
| Event-narrative completion | Nonblank event narratives / all events | `analysis.py` | Measures presence, not narrative accuracy |
| Vehicle share, all direct records | Direct-fatality records labeled Vehicle/Towed Trailer / all direct-fatality records | `06_fatality_context.sql` | Uses 391 child records, including the source-count discrepancy |
| Vehicle share, known context | Same numerator / direct records with context other than Unknown or Other | `06_fatality_context.sql` | Uses 333 records; missing context can be nonrandom |
| Fatality reconciliation gap | Child direct/indirect counts minus corresponding event-summary counts, per event | `07_fatality_reconciliation.sql` | Retained as a source inconsistency, not a correction |
| Routine-event retention | Events with no statistical outlier flags and a valid duration / full population | `09_outlier_sensitivity.sql` | A comparison population; never the headline loss denominator |
| Routine loss retention | Reported property loss in routine population / full-population loss | `09_outlier_sensitivity.sql` | Sensitivity measure; deleting the tail deletes most observed loss |
| Naïve-join inflation factor | Sum of event property loss after direct child joins / event-grain property loss | `analysis.py` | A measured model-failure demonstration, excluded from production KPIs |

## Outlier definitions

The duration flag uses the upper Tukey fence: `Q3 + 1.5 × (Q3 - Q1)` on nonnegative recorded durations. The frozen snapshot yields **6 hours**. Values strictly above the fence are flagged; values at the fence remain.

The damage flag uses the same upper fence on `log(1 + property_damage_usd)` among strictly positive values, then applies the inverse `exp(fence) - 1`. Its snapshot threshold is **$3,400,537.78**. The transform avoids the degenerate result of an IQR rule on a population whose median is zero.

The two flags overlap on 67 events. There are 1,086 duration flags and 160 damage flags, producing **1,179 distinct routine exclusions**. No winsorization, silent replacement, or deletion from the full impact table occurs.

Thresholds are estimated once on the full study population and remain fixed in the browser report. Filtering to one state does not redefine what counts as a statistical tail.
