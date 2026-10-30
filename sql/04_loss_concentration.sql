-- Top 1% of ALL events, not only events with positive reported damage.
WITH ranked AS (
    SELECT event_id, property_damage_usd,
           ROW_NUMBER() OVER (ORDER BY property_damage_usd DESC, event_id) AS loss_rank,
           COUNT(*) OVER () AS n, SUM(property_damage_usd) OVER () AS total_loss
    FROM fact_event
)
SELECT 'Top 1% of events' AS population, CAST((n + 99) / 100 AS INTEGER) AS selected_records,
       SUM(CASE WHEN loss_rank <= CAST((n + 99) / 100 AS INTEGER) THEN property_damage_usd ELSE 0 END) AS selected_loss_usd,
       MAX(total_loss) AS all_loss_usd,
       100.0 * SUM(CASE WHEN loss_rank <= CAST((n + 99) / 100 AS INTEGER) THEN property_damage_usd ELSE 0 END) / MAX(total_loss) AS loss_share_pct
FROM ranked
UNION ALL
SELECT 'Top 10 events', 10,
       SUM(CASE WHEN loss_rank <= 10 THEN property_damage_usd ELSE 0 END), MAX(total_loss),
       100.0 * SUM(CASE WHEN loss_rank <= 10 THEN property_damage_usd ELSE 0 END) / MAX(total_loss)
FROM ranked;
