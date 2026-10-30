-- Grain: one row per event; all in-scope events, including statistical extremes.
SELECT COUNT(*) AS recorded_events,
       COUNT(DISTINCT episode_id) AS recorded_episodes,
       COUNT(DISTINCT geography_key) AS counties_with_records,
       SUM(property_damage_usd) AS reported_property_damage_usd,
       SUM(crop_damage_usd) AS reported_crop_damage_usd,
       SUM(deaths_direct) AS reported_direct_deaths,
       SUM(deaths_indirect) AS reported_indirect_deaths,
       SUM(injuries_direct) AS reported_direct_injuries,
       SUM(injuries_indirect) AS reported_indirect_injuries,
       SUM(CASE WHEN property_damage_status = 'positive' THEN 1 ELSE 0 END) AS positive_property_events,
       SUM(CASE WHEN property_damage_status = 'zero' THEN 1 ELSE 0 END) AS zero_property_events,
       SUM(CASE WHEN property_damage_status IN ('missing','invalid') THEN 1 ELSE 0 END) AS unknown_property_events,
       SUM(CASE WHEN deaths_direct > 0 THEN 1 ELSE 0 END) AS direct_fatal_events,
       AVG(duration_hours) AS mean_recorded_duration_hours,
       AVG(CASE WHEN property_damage_usd > 0 THEN property_damage_usd END) AS mean_positive_property_damage_usd
FROM fact_event;
