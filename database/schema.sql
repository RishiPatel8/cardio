-- CardioGuard AI Relational Schema for PostgreSQL

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users Profile Data Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_sync TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Wearable & ECG Telemetry Data Stream Log
CREATE TABLE telemetry_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    data_source VARCHAR(50) NOT NULL, -- 'google_fit' or 'csv_upload'
    file_name VARCHAR(255),
    average_bpm FLOAT NOT NULL,
    sdrr_ms FLOAT NOT NULL,
    rmssd_ms FLOAT NOT NULL,
    timeseries_data JSONB NOT NULL, -- hourly BPM logs or R-R peak times
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- AI CNN-LSTM Diagnostic Classifier Logs
CREATE TABLE ai_diagnostics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telemetry_id UUID REFERENCES telemetry_logs(id) ON DELETE CASCADE,
    classification VARCHAR(50) NOT NULL, -- 'Normal' or 'AF Risk'
    confidence_score FLOAT NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    explainable_insights TEXT[] NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexing for rapid queries on timeseries calculations
CREATE INDEX idx_telemetry_user ON telemetry_logs(user_id);
CREATE INDEX idx_telemetry_created ON telemetry_logs(created_at);
CREATE INDEX idx_diagnostics_classification ON ai_diagnostics(classification);
