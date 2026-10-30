-- Fatality records are used for context; event summary counts remain authoritative KPIs.
WITH direct AS (
    SELECT * FROM fact_fatality WHERE fatality_type = 'D'
), counts AS (
    SELECT fatality_location, COUNT(*) AS direct_fatality_records,
           SUM(CASE WHEN age_years IS NULL THEN 1 ELSE 0 END) AS unknown_age_records
    FROM direct GROUP BY fatality_location
)
SELECT *, 100.0 * direct_fatality_records / (SELECT COUNT(*) FROM direct) AS share_all_direct_records_pct,
       CASE WHEN fatality_location NOT IN ('Unknown','Other') THEN
           100.0 * direct_fatality_records / NULLIF((SELECT COUNT(*) FROM direct WHERE fatality_location NOT IN ('Unknown','Other')),0)
       END AS share_known_location_direct_records_pct
FROM counts ORDER BY direct_fatality_records DESC, fatality_location;
