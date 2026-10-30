PRAGMA foreign_keys = ON;

CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY, calendar_date TEXT NOT NULL UNIQUE,
    year INTEGER NOT NULL, month INTEGER NOT NULL, month_name TEXT NOT NULL,
    quarter INTEGER NOT NULL, day_of_week TEXT NOT NULL, is_weekend INTEGER NOT NULL
);
CREATE TABLE dim_geography (
    geography_key TEXT PRIMARY KEY, state_fips INTEGER NOT NULL, state TEXT NOT NULL,
    cz_type TEXT NOT NULL, cz_fips INTEGER NOT NULL, cz_name TEXT NOT NULL
);
CREATE TABLE dim_episode (
    episode_id INTEGER PRIMARY KEY, first_event_at TEXT, last_event_at TEXT,
    event_count INTEGER NOT NULL CHECK (event_count > 0)
);
CREATE TABLE fact_event (
    event_id INTEGER PRIMARY KEY,
    episode_id INTEGER NOT NULL REFERENCES dim_episode(episode_id),
    geography_key TEXT NOT NULL REFERENCES dim_geography(geography_key),
    date_key INTEGER REFERENCES dim_date(date_key),
    year INTEGER NOT NULL, month INTEGER, begin_hour INTEGER,
    begin_at TEXT, end_at TEXT, reported_timezone TEXT,
    duration_hours REAL CHECK (duration_hours >= 0),
    is_overnight_start INTEGER CHECK (is_overnight_start IN (0, 1)),
    property_damage_raw TEXT, property_damage_usd REAL CHECK (property_damage_usd >= 0),
    property_damage_status TEXT NOT NULL,
    crop_damage_raw TEXT, crop_damage_usd REAL CHECK (crop_damage_usd >= 0),
    crop_damage_status TEXT NOT NULL,
    deaths_direct INTEGER CHECK (deaths_direct >= 0),
    deaths_indirect INTEGER CHECK (deaths_indirect >= 0),
    injuries_direct INTEGER CHECK (injuries_direct >= 0),
    injuries_indirect INTEGER CHECK (injuries_indirect >= 0),
    source TEXT, flood_cause TEXT, event_narrative TEXT,
    duration_outlier INTEGER NOT NULL, damage_outlier INTEGER NOT NULL,
    source_file TEXT NOT NULL, source_row INTEGER NOT NULL
);
CREATE TABLE fact_location (
    event_id INTEGER NOT NULL REFERENCES fact_event(event_id), location_index INTEGER NOT NULL,
    location TEXT, latitude REAL, longitude REAL, latitude_raw TEXT, longitude_raw TEXT,
    coordinate_valid INTEGER NOT NULL, source_file TEXT NOT NULL, source_row INTEGER NOT NULL,
    PRIMARY KEY (event_id, location_index)
);
CREATE TABLE fact_fatality (
    fatality_id INTEGER PRIMARY KEY, event_id INTEGER NOT NULL REFERENCES fact_event(event_id),
    fatality_type TEXT, age_years INTEGER, fatality_sex TEXT, fatality_location TEXT,
    source_file TEXT NOT NULL, source_row INTEGER NOT NULL
);
CREATE TABLE data_issue (
    issue_id TEXT PRIMARY KEY, table_name TEXT NOT NULL, event_id TEXT, source_file TEXT,
    source_row INTEGER, rule TEXT NOT NULL, column_name TEXT, raw_value TEXT,
    action TEXT NOT NULL, severity TEXT NOT NULL
);

CREATE INDEX idx_event_episode ON fact_event(episode_id);
CREATE INDEX idx_event_geo_date ON fact_event(geography_key, date_key);
CREATE INDEX idx_fatality_event ON fact_fatality(event_id);

-- Aggregate each one-to-many child before joining; the output stays one row/event.
CREATE VIEW vw_event_enriched AS
WITH locations AS (
    SELECT event_id, COUNT(*) AS location_records,
           SUM(coordinate_valid) AS valid_location_records
    FROM fact_location GROUP BY event_id
), fatalities AS (
    SELECT event_id, COUNT(*) AS fatality_records,
           SUM(CASE WHEN fatality_type = 'D' THEN 1 ELSE 0 END) AS direct_fatality_records,
           SUM(CASE WHEN fatality_type = 'I' THEN 1 ELSE 0 END) AS indirect_fatality_records
    FROM fact_fatality GROUP BY event_id
)
SELECT e.*, g.state, g.state_fips, g.cz_type, g.cz_fips, g.cz_name,
       COALESCE(l.location_records, 0) AS location_records,
       COALESCE(l.valid_location_records, 0) AS valid_location_records,
       COALESCE(f.fatality_records, 0) AS fatality_records,
       COALESCE(f.direct_fatality_records, 0) AS direct_fatality_records,
       COALESCE(f.indirect_fatality_records, 0) AS indirect_fatality_records
FROM fact_event e
JOIN dim_geography g USING (geography_key)
LEFT JOIN locations l USING (event_id)
LEFT JOIN fatalities f USING (event_id);

-- Deliberate outlier removal for a comparison population, not loss accounting.
CREATE VIEW vw_routine_event AS
SELECT * FROM vw_event_enriched
WHERE duration_outlier = 0 AND damage_outlier = 0 AND duration_hours IS NOT NULL;
