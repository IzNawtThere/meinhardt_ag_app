import pandas as pd
from sqlalchemy import text
from db import engine

def save_ag_version(version_name: str):
    with engine.begin() as conn:
        master_df = pd.read_sql("SELECT * FROM pilot_ag_master", conn)
        version_table = f"ag_snapshot__{version_name}"
        master_df.to_sql(version_table, con=conn, if_exists="replace", index=False)

        existing = conn.execute(text("""
            SELECT COUNT(*) FROM ag_versions WHERE version_name = :version_name
        """), {"version_name": version_name}).scalar()

        if not existing:
            conn.execute(text("""
                INSERT INTO ag_versions (version_name)
                VALUES (:version_name)
            """), {"version_name": version_name})

    log_ag_action("admin", "manual_save", version_name)
    return f"Saved version '{version_name}' as table '{version_table}'"

def restore_ag_version(version_name: str):
    version_table = f"ag_snapshot__{version_name}"
    with engine.begin() as conn:
        df_snapshot = pd.read_sql(f"SELECT * FROM {version_table}", conn)
        df_snapshot.to_sql("pilot_ag_master", conn, if_exists="replace", index=False)

    log_ag_action("admin", "restore", version_name)
    return f"Restored version '{version_name}' to 'pilot_ag_master'"

def log_ag_action(username: str, action: str, version_name: str):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO ag_audit_log (username, action, version_name)
            VALUES (:username, :action, :version_name)
        """), {
            "username": username,
            "action": action,
            "version_name": version_name
        })