from sqlalchemy import text
from db import engine


with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ag_versions (
            version_name TEXT PRIMARY KEY,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """))

with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ag_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            action TEXT,
            version_name TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """))

with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS devco_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version_name TEXT,
            devco_id TEXT,
            data_point_id TEXT,
            field_name TEXT,
            value TEXT,
            submitted_at TEXT,
            UNIQUE(devco_id, data_point_id, field_name)
        )
    """))
    conn.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_submission
        ON devco_submissions(devco_id, data_point_id, field_name);
    """))

with engine.begin() as conn:
    # conn.execute(text("DROP TABLE IF EXISTS assessment_matrix"))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS assessment_matrix (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_criteria TEXT NOT NULL,
            weightage REAL,
            formula TEXT,
            data_points_used TEXT,
            calculation_type TEXT,
            rating_good TEXT,
            rating_satisfactory TEXT,
            rating_needs_improvement TEXT,
            pillar TEXT,
            description TEXT, -- New field
            formula_type TEXT -- New field: 'manual' | 'auto' | 'custom'
        )
    """))

print("All tables created successfully with enforced uniqueness.")