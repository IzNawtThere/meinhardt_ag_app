from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///meinhardt.db')

with engine.begin() as conn:
    conn.execute(text("DELETE FROM pilot_ag_master"))
    print("pilot_ag_master wiped clean successfully.")
