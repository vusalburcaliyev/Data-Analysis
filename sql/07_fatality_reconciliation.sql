-- Never silently replace an event-level count with the child record count.
SELECT event_id, year, state, cz_name, deaths_direct, direct_fatality_records,
       direct_fatality_records - deaths_direct AS direct_difference,
       deaths_indirect, indirect_fatality_records,
       indirect_fatality_records - deaths_indirect AS indirect_difference,
       source_file, source_row
FROM vw_event_enriched
WHERE deaths_direct <> direct_fatality_records OR deaths_indirect <> indirect_fatality_records
ORDER BY event_id;
