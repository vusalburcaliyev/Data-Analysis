-- NOAA episode IDs are reporting groups; they are not nationwide unique meteorological storms.
SELECT episode_id, COUNT(*) AS events, COUNT(DISTINCT geography_key) AS affected_counties,
       COUNT(DISTINCT state) AS affected_states, MIN(begin_at) AS first_recorded_start,
       SUM(property_damage_usd) AS property_damage_usd, SUM(deaths_direct) AS direct_deaths,
       SUM(injuries_direct) AS direct_injuries
FROM vw_event_enriched GROUP BY episode_id ORDER BY property_damage_usd DESC, episode_id;
