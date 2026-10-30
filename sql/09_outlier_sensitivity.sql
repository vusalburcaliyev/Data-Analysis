SELECT 'Full population' AS population, COUNT(*) AS events,
       SUM(property_damage_usd) AS property_damage_usd,
       AVG(property_damage_usd) AS mean_property_damage_usd,
       SUM(deaths_direct) AS direct_deaths, AVG(duration_hours) AS mean_duration_hours
FROM fact_event
UNION ALL
SELECT 'Duration outliers removed', COUNT(*), SUM(property_damage_usd), AVG(property_damage_usd),
       SUM(deaths_direct), AVG(duration_hours) FROM fact_event WHERE duration_outlier = 0 AND duration_hours IS NOT NULL
UNION ALL
SELECT 'Damage outliers removed', COUNT(*), SUM(property_damage_usd), AVG(property_damage_usd),
       SUM(deaths_direct), AVG(duration_hours) FROM fact_event WHERE damage_outlier = 0
UNION ALL
SELECT 'Routine comparison population', COUNT(*), SUM(property_damage_usd), AVG(property_damage_usd),
       SUM(deaths_direct), AVG(duration_hours) FROM vw_routine_event;
