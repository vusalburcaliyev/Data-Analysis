SELECT geography_key, state, cz_name AS county_name, COUNT(*) AS events,
       COUNT(DISTINCT year) AS years_with_records,
       SUM(property_damage_usd) AS property_damage_usd, SUM(deaths_direct) AS direct_deaths,
       SUM(injuries_direct) AS direct_injuries,
       SUM(property_damage_status = 'positive') AS positive_damage_events,
       SUM(is_overnight_start) AS overnight_start_events
FROM vw_event_enriched GROUP BY geography_key, state, cz_name ORDER BY events DESC, geography_key;
