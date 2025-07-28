import pandas as pd
from sqlalchemy import create_engine

# Load Excel (the file you just saved)
df = pd.read_excel('assessment_matrix.xlsx')

# Clean column names
df.columns = [c.strip() for c in df.columns]

# Connect to the database
engine = create_engine('sqlite:///meinhardt.db')

# Upload clean matrix to DB
df.to_sql('assessment_matrix', engine, if_exists='replace', index=False)

print("Assessment matrix uploaded successfully.")
