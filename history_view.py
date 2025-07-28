import streamlit as st
import pandas as pd
from sqlalchemy import text
from db import engine

def render():
    st.header("Submission History Viewer")

    with engine.connect() as conn:
        ag_df = pd.read_sql("SELECT DISTINCT data_point_id FROM pilot_ag_master WHERE data_point_id IS NOT NULL", conn)

    dp_ids = ag_df['data_point_id'].dropna().unique().tolist()
    if not dp_ids:
        st.warning("No data points found.")
        return

    col1, col2 = st.columns(2)
    data_point_id = col1.selectbox("Select Data Point ID", dp_ids)

    # Pull distinct DevCo IDs and version names for filtering
    with engine.connect() as conn:
        filters_df = pd.read_sql(
            text("SELECT DISTINCT devco_id, version_name FROM devco_submissions"),
            conn
        )

    devco_ids = sorted(filters_df['devco_id'].dropna().unique().tolist())
    version_names = sorted(filters_df['version_name'].dropna().unique().tolist())

    devco_filter = col2.selectbox("Filter by DevCo", ["All"] + devco_ids)
    version_filter = st.selectbox("Filter by Version", ["All"] + version_names)

    with engine.connect() as conn:
        # Build dynamic query with filters
        query = """
            SELECT submitted_at, devco_id, value, field_name, version_name
            FROM devco_submissions
            WHERE data_point_id = :dpid
        """

        if devco_filter != "All":
            query += " AND devco_id = :devco"
        if version_filter != "All":
            query += " AND version_name = :version"

        query += " ORDER BY submitted_at DESC"

        params = {"dpid": data_point_id}
        if devco_filter != "All":
            params["devco"] = devco_filter
        if version_filter != "All":
            params["version"] = version_filter

        history_df = pd.read_sql(text(query), conn, params=params)

        # Pivot field_name → columns
        history_df = history_df.rename(columns={
            "submitted_at": "timestamp",
            "devco_id": "username"
        })
        history_df["comments"] = ""

        # Rename columns to match expected format
        history_df = history_df.rename(columns={
            "submitted_at": "timestamp",
            "devco_id": "username"
        })
        # There is no 'comments' column in your data, so we add a dummy one.
        history_df["comments"] = ""

    if history_df.empty:
        st.info("No submissions found for this field.")
        return

    def compute_change_log(df):
        diffs = []
        for i in range(len(df)):
            if i == len(df) - 1:
                diffs.append("Initial entry")
            else:
                prev = df.loc[i+1]
                curr = df.loc[i]
                changes = []
                val_curr = "" if pd.isna(curr["value"]) or str(curr["value"]).lower() in ["nan", "undefined"] else str(curr["value"])
                val_prev = "" if pd.isna(prev["value"]) or str(prev["value"]).lower() in ["nan", "undefined"] else str(prev["value"])

                com_curr = "" if pd.isna(curr["comments"]) or str(curr["comments"]).lower() in ["nan", "undefined"] else str(curr["comments"])
                com_prev = "" if pd.isna(prev["comments"]) or str(prev["comments"]).lower() in ["nan", "undefined"] else str(prev["comments"])

                if val_curr != val_prev:
                    changes.append(f"Value: '{val_prev}' → '{val_curr}'")
                if com_curr != com_prev:
                    changes.append(f"Comment: '{com_prev}' → '{com_curr}'")

                diffs.append(" | ".join(changes) if changes else "No change")
        return diffs

    history_df["change_log"] = compute_change_log(history_df)

    def color_for_log(log):
        if "Initial entry" in log:
            return "#2196F3"  # blue
        elif "→" in log:
            return "#4CAF50"  # green
        else:
            return "#9E9E9E"  # gray

    view_mode = st.radio("View Mode", ["Visual Cards", "Compact Table", "Submission Matrix"], horizontal=True)

    st.subheader("Submission History Log")

    # Replace nan/undefined with blank for clean display
    if "value" in history_df.columns:
        history_df["value"] = history_df["value"].replace(["nan", "undefined"], "").fillna("")
    else:
        history_df["value"] = ""

    history_df["comments"] = ""

    if view_mode == "Compact Table":
        clean_df = history_df[["timestamp", "username", "version_name", "value", "comments", "change_log"]].copy()
        clean_df = clean_df.rename(columns={
            "timestamp": "Timestamp",
            "username": "User",
            "version_name": "Version",
            "value": "Value",
            "comments": "Comment",
            "change_log": "Change"
        })
        st.dataframe(clean_df, use_container_width=True)
        csv = clean_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"history_{data_point_id}.csv",
            mime='text/csv'
        )

    elif view_mode == "Visual Cards":
        for _, row in history_df.iterrows():
            bg = color_for_log(row["change_log"])
            st.markdown(f"""
            <div style="background-color:{bg}; padding:10px; border-radius:8px; margin-bottom:10px; color:white;">
                <b>{row['timestamp']}</b> by <b>{row['username']}</b> | Version: <b>{row['version_name']}</b><br>
                Value: <code>{row['value']}</code><br>
                Comment: <code>{row['comments']}</code><br>
                <i>{row['change_log']}</i>
            </div>
            """, unsafe_allow_html=True)

    elif view_mode == "Submission Matrix":
        st.subheader("DevCo Submission Matrix")
        matrix_df = history_df.pivot_table(
            index="version_name",
            columns="username",
            values="value",
            aggfunc="first"
        ).sort_index(ascending=False)
        st.dataframe(matrix_df, use_container_width=True)