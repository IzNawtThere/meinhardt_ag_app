import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///meinhardt.db')

with engine.connect() as conn:
    df = pd.read_sql("SELECT * FROM pilot_ag_master", conn)

df.to_csv("backup_pilot_ag_master.csv", index=False)
print("Backup saved as backup_pilot_ag_master.csv")
