from sqlalchemy import create_engine, text

# Update this to match your current engine connection string
engine = create_engine('sqlite:///meinhardt.db')  # Or whatever your SQLite file path is

with engine.begin() as conn:
    conn.execute(text("""
        ALTER TABLE devco_submissions ADD COLUMN timestamp TEXT;
    """))

print("Column 'timestamp' added to devco_submissions successfully.")