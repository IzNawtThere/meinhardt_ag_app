from db import engine
from sqlalchemy import text

with engine.begin() as conn:
    conn.execute(text("DELETE FROM devco_submissions"))
    print("devco_submissions wiped clean.")
