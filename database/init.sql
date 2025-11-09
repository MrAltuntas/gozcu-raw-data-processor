-- TimescaleDB initialization script
-- Creates tables for camera events and detections

-- Ensure TimescaleDB extension is available
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Camera events raw data table
CREATE TABLE IF NOT EXISTS camera_events_raw (
    camera_id INTEGER NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    frame_number INTEGER,
    has_detection BOOLEAN NOT NULL DEFAULT FALSE,
    detection_count INTEGER NOT NULL DEFAULT 0,
    processing_time_ms INTEGER,
    stream_lag_ms INTEGER,
    
    -- Constraints
    CONSTRAINT camera_events_raw_camera_id_positive CHECK (camera_id > 0),
    CONSTRAINT camera_events_raw_frame_number_non_negative CHECK (frame_number >= 0),
    CONSTRAINT camera_events_raw_detection_count_non_negative CHECK (detection_count >= 0),
    CONSTRAINT camera_events_raw_processing_time_positive CHECK (processing_time_ms > 0),
    CONSTRAINT camera_events_raw_stream_lag_non_negative CHECK (stream_lag_ms >= 0)
);

-- Camera detections raw data table
CREATE TABLE IF NOT EXISTS camera_detections_raw (
    event_time TIMESTAMPTZ NOT NULL,
    camera_id INTEGER NOT NULL,
    class_id INTEGER NOT NULL,
    confidence INTEGER NOT NULL,
    photo_url TEXT,
    coord_x INTEGER,
    coord_y INTEGER,
    region_ids INTEGER[],
    bbox_width INTEGER,
    bbox_height INTEGER,
    object_id TEXT,
    track_id INTEGER,
    
    -- Constraints
    CONSTRAINT camera_detections_raw_camera_id_positive CHECK (camera_id > 0),
    CONSTRAINT camera_detections_raw_class_id_positive CHECK (class_id > 0),
    CONSTRAINT camera_detections_raw_confidence_range CHECK (confidence >= 0 AND confidence <= 100),
    CONSTRAINT camera_detections_raw_coord_x_non_negative CHECK (coord_x >= 0),
    CONSTRAINT camera_detections_raw_coord_y_non_negative CHECK (coord_y >= 0),
    CONSTRAINT camera_detections_raw_bbox_width_positive CHECK (bbox_width > 0),
    CONSTRAINT camera_detections_raw_bbox_height_positive CHECK (bbox_height > 0),
    CONSTRAINT camera_detections_raw_track_id_positive CHECK (track_id > 0)
);

-- Convert tables to hypertables for time-series optimization
SELECT create_hypertable('camera_events_raw', 'event_time', if_not_exists => TRUE);
SELECT create_hypertable('camera_detections_raw', 'event_time', if_not_exists => TRUE);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_camera_events_raw_camera_id_time 
ON camera_events_raw (camera_id, event_time DESC);

CREATE INDEX IF NOT EXISTS idx_camera_events_raw_has_detection 
ON camera_events_raw (has_detection, event_time DESC) 
WHERE has_detection = TRUE;

CREATE INDEX IF NOT EXISTS idx_camera_detections_raw_camera_id_time 
ON camera_detections_raw (camera_id, event_time DESC);

CREATE INDEX IF NOT EXISTS idx_camera_detections_raw_class_confidence 
ON camera_detections_raw (class_id, confidence, event_time DESC);

CREATE INDEX IF NOT EXISTS idx_camera_detections_raw_track_id 
ON camera_detections_raw (track_id, event_time DESC) 
WHERE track_id IS NOT NULL;

-- Set retention policy (optional - keep data for 1 year)
SELECT add_retention_policy('camera_events_raw', INTERVAL '1 year', if_not_exists => TRUE);
SELECT add_retention_policy('camera_detections_raw', INTERVAL '1 year', if_not_exists => TRUE);

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON camera_events_raw TO your_app_user;
-- GRANT ALL PRIVILEGES ON camera_detections_raw TO your_app_user;

-- Confirmation message
DO $$
BEGIN
    RAISE NOTICE 'Tables created successfully:';
    RAISE NOTICE '- camera_events_raw (hypertable)';
    RAISE NOTICE '- camera_detections_raw (hypertable)';
    RAISE NOTICE 'Indexes and retention policies configured.';
END
$$;