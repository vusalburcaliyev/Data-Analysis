SELECT month, begin_hour, COUNT(*) AS events,
       SUM(deaths_direct) AS direct_deaths, SUM(property_damage_usd) AS property_damage_usd
FROM fact_event WHERE month IS NOT NULL AND begin_hour IS NOT NULL
GROUP BY month, begin_hour ORDER BY month, begin_hour;
