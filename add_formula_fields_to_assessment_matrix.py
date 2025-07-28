from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///meinhardt.db')

with engine.begin() as conn:
    conn.execute(text("""
        ALTER TABLE assessment_matrix ADD COLUMN formula TEXT
    """))
    conn.execute(text("""
        ALTER TABLE assessment_matrix ADD COLUMN thresholds TEXT
    """))
    conn.execute(text("""
        ALTER TABLE assessment_matrix ADD COLUMN data_point_refs TEXT
    """))

print("Columns 'formula', 'thresholds', and 'data_point_refs' added to assessment_matrix successfully.")