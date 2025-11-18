-- Initialize the database schema
-- This file will be executed when the PostgreSQL container starts for the first time

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables (will be managed by SQLAlchemy, this is just for documentation)
-- The actual tables will be created by the backend application on startup

