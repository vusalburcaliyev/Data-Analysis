# Interpretation boundaries

1. **Observed reporting, not complete incidence.** NOAA records significant events according to source reporting processes. Recorded counts combine actual impacts with reporting practices and cannot be interpreted as a complete census of flooding.
2. **County event grain.** An event ID represents a reported county-level event, not necessarily a unique national storm. Episode IDs are NOAA reporting groups; the same meteorological system can be represented by multiple groups.
3. **Estimated monetary values.** Property and crop damage are broad, nominal estimates. They are not verified claims, audited asset losses, inflation-adjusted economic damage, or an insurance pricing basis.
4. **Zero ambiguity.** The snapshot does not distinguish an assessed absence of damage from a zero entry where damage has not been quantified. Zero remains a valid recorded value, accompanied by a diagnostic flag in analysis.
5. **Unequal exposure.** No population, road traffic, asset value, building stock, rainfall intensity, warning lead time, or response duration is joined. Counts and damage totals are not exposure-normalized risk rankings.
6. **Unadjusted overnight association.** The 20:00–05:59 start-time grouping uses source-reported local time. It does not measure darkness, the hour of a death, causal effects, or the impact of a safety intervention. Events within an episode may be dependent; no independent-event significance test is claimed.
7. **Known source disagreement.** One event has different direct-death counts in the summary and fatality-child tables. Both are preserved, and their separate analytical uses are stated.
8. **Incomplete linked locations.** The locations child table covers a varying fraction of events by year. Coverage does not measure geocoding accuracy and does not assess the details-file begin/end coordinates.
9. **Unresolved recorded durations.** Nine durations exceed 72 hours and 1,269 equal zero. No invented timestamp corrections are applied. The full-population median and sensitivity views expose their effect.
10. **Full-study thresholds.** Routine-view outlier thresholds are calibrated on the entire five-year snapshot. They describe this sample and should not be treated as universal definitions or used as training-only preprocessing in a predictive model without redesign.
11. **Historical revisions.** NOAA can revise past years. Findings refer to the exact locked snapshot, not a claim that the most recent live dataset will yield identical results.
12. **No implemented operational effect.** Suggested next steps are review and data-enrichment priorities. This project does not claim that an agency adopted them or that lives, time, or money were saved.
