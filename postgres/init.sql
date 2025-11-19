-- Initialize the database schema
-- This file will be executed when the PostgreSQL container starts for the first time

-- Note: The database is created automatically by the POSTGRES_DB environment variable
-- This script runs in the context of that database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables (will be managed by SQLAlchemy)
-- The actual tables will be created by the backend application on startup via SQLAlchemy

-- Grant all privileges (if needed for additional users)
-- GRANT ALL PRIVILEGES ON DATABASE newscatcher_db TO newscatcher;

