from sqlalchemy import create_engine, text
import pandas as pd

engine = create_engine('sqlite:///meinhardt.db')

with engine.begin() as conn:
    df = pd.read_sql(text("SELECT data_points_used FROM assessment_matrix"), conn)

print(df)
