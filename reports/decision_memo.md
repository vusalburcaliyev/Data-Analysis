# Flash-flood impact review

**Scope:** NOAA-reported Flash Flood events, 50 states and Washington, D.C., 2020–2024. Frozen source snapshot retrieved October 30, 2026.

## Decision

Use a two-part review: one queue for high-impact episodes and another for recurring event activity. Put reporting diagnostics beside both. The data supports prioritizing further investigation; it does not establish a causal intervention or an optimal allocation.

## What drives that decision

**A small tail dominates reported losses.** The 192 highest-loss event records account for 95.2% of the $8.78B property-damage total. Concentration remains high after aggregating to episode IDs: the highest-loss 1% of reporting groups accounts for 93.2%. The median positive damage entry is $10,000, while the mean positive entry is $1.54M. A single average hides the distribution.

**Volume and impact produce different review lists.** Texas has 1,504 records, the largest state event count. North Carolina has the largest recorded property-damage total, $2.16B, and 82 reported direct deaths. Its totals are heavily influenced by severe episodes. These are recorded burdens, not comparisons of intrinsic flood risk.

**Overnight starts deserve an adjusted follow-up.** Overnight-start records are 28.8% of events and contain 53.0% of reported direct deaths. A direct death is reported in 1.79% of overnight-start events, compared with 0.72% of other-start events. The 2.47× ratio is descriptive. Severity, geography, seasonality, and population exposure have not been controlled.

**The available financial and spatial records are uneven.** Explicit zero property-damage entries occur in 70.2% of records, including 101 of the 218 direct-casualty events. The child locations table covers 70.3% of events, decreasing from 98.0% in 2020 to 57.0% in 2024. The data cannot determine whether reporting practices or other factors explain those differences.

## Proposed review actions

| Review action | Evidence supporting it | Additional data / validation required | Success measure for a follow-up |
|---|---|---|---|
| Review the highest-loss reporting groups individually | Top-1% concentration persists at event and episode grain | Check original source narratives, monetary estimate basis, and overlap among related event records | Share of high-impact groups with a documented, reviewed estimate |
| Add zero, missing, and assessed-zero status to the loss workflow | Populated numeric fields do not resolve zero ambiguity | A genuine assessment-status field from the source process | Share of loss entries with an explicit assessment status |
| Validate spatial linkage before presenting comparative maps | Linked-location coverage changes materially by year | Profile details coordinates and child locations; inspect geographic and office-level coverage | Event-level geocoding coverage and documented coordinate provenance |
| Investigate the overnight casualty pattern | Higher recorded fatal-event proportion for overnight starts | Severity, rainfall, exposure, warning and closure records; account for episode grouping | Whether the descriptive association persists after adjustment |
| Resolve the casualty discrepancy with the source | Event 970467 has a +2 child-record discrepancy | Source review of the event summary and fatality rows | Reconciled count with a traceable revision record |

These measures are proposed checks for a future workflow. They are not achieved business outcomes.

## What changes if outliers are removed

The routine comparison excludes 1,179 events, 6.1% of records. It retains only $422.3M of property damage, 4.8% of the full total. Mean recorded duration decreases from 2.65 to 2.08 hours. The filter is suitable for routine-duration exploration and would be misleading for total-impact reporting.

## Confidence in the calculations

The event model uses explicit keys and child pre-aggregation. Directly joining both child tables would inflate the property-damage total by 4.92×. SQL results reconcile against independent pandas calculations; the committed source extracts are checksum-verified. The remaining uncertainty concerns what the recorded fields represent, not whether a duplicated join has distorted their sum.

See the [metric dictionary](../docs/metric_dictionary.md), [quality decisions](../docs/data_quality.md), and [limitations](../docs/limitations.md) for the full interpretation boundaries.
