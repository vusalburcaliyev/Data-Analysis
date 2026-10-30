-- Counts describe recorded impacts, not population-normalized hazard or risk.
SELECT state, COUNT(*) AS events,
       COUNT(DISTINCT geography_key) AS counties_with_records,
       SUM(property_damage_usd) AS property_damage_usd,
       SUM(deaths_direct) AS direct_deaths,
       SUM(injuries_direct) AS direct_injuries,
       100.0 * SUM(property_damage_status = 'positive') / COUNT(*) AS positive_damage_pct,
       100.0 * SUM(property_damage_status = 'zero') / COUNT(*) AS zero_damage_pct,
       1000.0 * SUM(deaths_direct) / COUNT(*) AS direct_deaths_per_1000_recorded_events,
       AVG(duration_hours) AS mean_duration_hours,
       SUM(CASE WHEN property_damage_usd > 0 THEN 1 ELSE 0 END) AS positive_loss_events
FROM vw_event_enriched GROUP BY state ORDER BY property_damage_usd DESC, state;
