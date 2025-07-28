import pandas as pd
from sqlalchemy import create_engine

# Load Excel (adjust file name and sheet name if needed)
df = pd.read_excel("clean_master_ag.xlsx", sheet_name="Planning & Monitoring")

# Clean columns: rename if needed to match DB schema exactly
df.rename(columns=lambda x: x.strip(), inplace=True)  # Removes extra whitespace

# Connect DB
engine = create_engine('sqlite:///meinhardt.db')

# Upload fresh AG Master
df.to_sql("pilot_ag_master", engine, if_exists="append", index=False)

print("Fresh pilot_ag_master uploaded successfully.")
