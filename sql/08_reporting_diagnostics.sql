-- Reporter mix can affect observed loss patterns. A zero entry is not a missing field.
SELECT source AS report_source, COUNT(*) AS events,
       SUM(property_damage_status = 'zero') AS zero_damage_events,
       100.0 * SUM(property_damage_status = 'zero') / COUNT(*) AS zero_damage_pct,
       SUM(CASE WHEN deaths_direct + injuries_direct > 0 THEN 1 ELSE 0 END) AS direct_casualty_events,
       SUM(CASE WHEN deaths_direct + injuries_direct > 0 AND property_damage_status = 'zero' THEN 1 ELSE 0 END) AS direct_casualty_events_with_zero_damage,
       SUM(CASE WHEN valid_location_records > 0 THEN 1 ELSE 0 END) AS events_with_valid_location,
       SUM(CASE WHEN event_narrative IS NULL THEN 1 ELSE 0 END) AS missing_event_narrative
FROM vw_event_enriched GROUP BY source ORDER BY events DESC;
