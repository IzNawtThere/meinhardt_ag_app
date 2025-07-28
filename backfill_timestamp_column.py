from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import random

engine = create_engine('sqlite:///meinhardt.db')

with engine.begin() as conn:
    # Generate random timestamps for existing rows
    result = conn.execute(text("SELECT id FROM devco_submissions")).fetchall()
    now = datetime.now()

    for idx, row in enumerate(result):
        random_days = random.randint(0, 365)
        fake_timestamp = (now - timedelta(days=random_days)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            text("UPDATE devco_submissions SET timestamp = :ts WHERE id = :id"),
            {"ts": fake_timestamp, "id": row[0]}
        )

print("Backfilled 'timestamp' column successfully.")