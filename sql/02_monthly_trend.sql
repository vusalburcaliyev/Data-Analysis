-- The calendar spine retains months with zero records; LAG compares like months.
WITH months AS (
    SELECT year, month, MIN(calendar_date) AS month_start
    FROM dim_date GROUP BY year, month
), aggregated AS (
    SELECT year, month, COUNT(*) AS events,
           SUM(property_damage_usd) AS property_damage_usd,
           SUM(deaths_direct) AS direct_deaths,
           SUM(injuries_direct) AS direct_injuries
    FROM fact_event GROUP BY year, month
), spine AS (
    SELECT m.*, COALESCE(a.events,0) AS events,
           COALESCE(a.property_damage_usd,0) AS property_damage_usd,
           COALESCE(a.direct_deaths,0) AS direct_deaths,
           COALESCE(a.direct_injuries,0) AS direct_injuries
    FROM months m LEFT JOIN aggregated a USING (year,month)
)
SELECT *, LAG(events,12) OVER (ORDER BY month_start) AS prior_year_events,
       100.0 * (events - LAG(events,12) OVER (ORDER BY month_start)) /
           NULLIF(LAG(events,12) OVER (ORDER BY month_start),0) AS event_yoy_pct
FROM spine ORDER BY month_start;
