-- Overnight means 20:00-05:59 in NOAA's reported local time; not sunset/sunrise.
-- Start time classifies the event, not the time of a casualty.
SELECT CASE is_overnight_start WHEN 1 THEN 'Overnight start' ELSE 'Other start' END AS start_period,
       COUNT(*) AS events, SUM(deaths_direct) AS direct_deaths,
       SUM(CASE WHEN deaths_direct > 0 THEN 1 ELSE 0 END) AS direct_fatal_events,
       100.0 * SUM(CASE WHEN deaths_direct > 0 THEN 1 ELSE 0 END) / COUNT(*) AS fatal_event_pct,
       1000.0 * SUM(deaths_direct) / COUNT(*) AS direct_deaths_per_1000_recorded_events,
       SUM(property_damage_usd) AS property_damage_usd
FROM fact_event WHERE is_overnight_start IS NOT NULL
GROUP BY is_overnight_start ORDER BY is_overnight_start DESC;
