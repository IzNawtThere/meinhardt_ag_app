from sqlalchemy import create_engine

# Change this to your actual DB path or connection string
engine = create_engine("sqlite:///meinhardt.db", echo=False)