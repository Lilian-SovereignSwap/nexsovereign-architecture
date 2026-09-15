CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TYPE severity_level AS ENUM ('HIGH', 'MED', 'LOW');
CREATE TYPE incident_status AS ENUM ('Open', 'In Review', 'Closed');

CREATE TABLE IF NOT EXISTS incidents (
    incident_id VARCHAR(30) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    sector VARCHAR(50) NOT NULL,
    severity severity_level NOT NULL,
    incident_type VARCHAR(100) NOT NULL,
    status incident_status NOT NULL DEFAULT 'Open',
    assigned_to VARCHAR(100) NOT NULL DEFAULT 'Unassigned',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sensor_telemetry (
    time TIMESTAMPTZ NOT NULL,
    sensor_id VARCHAR(50) NOT NULL,
    pressure_psi DOUBLE PRECISION,
    acoustic_db DOUBLE PRECISION,
    battery_life INT,
    network_quality INT
);

SELECT create_hypertable('sensor_telemetry', 'time', if_not_exists => TRUE);

INSERT INTO incidents (incident_id, title, sector, severity, incident_type, status, assigned_to) 
VALUES 
('#INC-104', 'Potential intrusion detected', 'Sector 14', 'HIGH', 'Intrusion', 'Open', 'Ops Team A'),
('#INC-103', 'Sensor drift warning', 'Sector 09', 'MED', 'Leak', 'In Review', 'Field Team 2')
ON CONFLICT (incident_id) DO NOTHING;
