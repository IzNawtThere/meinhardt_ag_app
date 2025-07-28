import streamlit as st
import pandas as pd
from db import engine
from datetime import datetime, date
from sqlalchemy import text


def render_dynamic_input(field_label, input_type, key, default_value=None):
    if pd.isna(default_value) or default_value is None:
        default_value = ""
    if input_type == "No.":
        return st.number_input(field_label, key=key, value=float(default_value) if default_value != "" else 0.0)
    elif input_type == "%":
        return st.slider(field_label, 0, 100, key=key, value=int(float(default_value)) if default_value != "" else 0)
    elif input_type == "dd/mm/yy":
        if default_value:
            try:
                default_date = pd.to_datetime(default_value, dayfirst=True, errors='coerce')
                if pd.isna(default_date):
                    default_date = date.today()
                else:
                    default_date = default_date.date()
            except:
                default_date = date.today()
        else:
            default_date = date.today()
        return st.date_input(field_label, key=key, value=default_date)
    else:
        return st.text_input(field_label, key=key, value=str(default_value))


def fetch_existing_submission(devco_id, data_point_id):
    with engine.begin() as conn:
        query = text("""
            SELECT field_name, value
            FROM devco_submissions
            WHERE devco_id = :devco_id AND data_point_id = :data_point_id
        """)
        result = conn.execute(query, {"devco_id": devco_id, "data_point_id": data_point_id}).mappings().all()
        existing = {}
        for row in result:
            existing[row["field_name"]] = row["value"]
        return existing


def render(username):
    st.header("DevCo Input Entry")
    devco_id = username.split("@")[0] if "@" in username else username

    with engine.begin() as conn:
        df = pd.read_sql("SELECT * FROM pilot_ag_master", conn)

        df = df[df["data_point_id"].notna()]
        df["data_point_id"] = df["data_point_id"].astype(str).str.strip()

    st.subheader(f"Current AG Table for DevCo: {devco_id}")
    devco_df = df[df["devco_id"] == devco_id]

    if devco_df.empty:
        st.warning("No AG rows found for this DevCo")
        return

    edited_rows = []

    st.write("Enter your Input Values below:")

    for i, row in devco_df.iterrows():
        st.markdown("---")
        st.markdown(f"**Data Point ID:** `{row['data_point_id']}`")
        st.markdown(f"**Data Point:** `{row['data_point']}`")
        st.markdown(f"**Input Type Detected:** `{row.get('input_type', 'Text')}`")

        existing = fetch_existing_submission(devco_id, row["data_point_id"])
        prev_input_value = existing.get("input_value")
        prev_remarks = existing.get("remarks")

        col1, col2 = st.columns(2)

        input_value = render_dynamic_input(
            f"Input Value for {row['data_point']}",
            row.get("input_type", "Text"),
            key=f"input_{i}",
            default_value=prev_input_value
        )
        remarks = col2.text_input(
            f"Remarks for {row['data_point']}",
            value=prev_remarks or "",
            key=f"remarks_{i}"
        )

        data_point_name = row["data_point"] or ""

        edited_rows.append({
            "version_name": "upload_latest",
            "devco_id": devco_id,
            "data_point_id": row["data_point_id"].strip(),
            "data_point": data_point_name.strip(),
            "field_name": "input_value",
            "value": None if input_value in [None, "", ""] else str(input_value)
        })

        edited_rows.append({
            "version_name": "upload_latest",
            "devco_id": devco_id,
            "data_point_id": row["data_point_id"].strip(),
            "data_point": data_point_name.strip(),
            "field_name": "remarks",
            "value": remarks.strip()
        })

    if edited_rows:
        st.subheader("Preview of Submission")
        st.dataframe(pd.DataFrame(edited_rows), use_container_width=True)

    if st.button("Submit All"):
        if not edited_rows:
            st.warning("No changes to submit.")
        else:
            try:
                with engine.begin() as conn:
                    for entry in edited_rows:
                        conn.execute(
                            text("""
                            INSERT INTO devco_submissions
                            (version_name, devco_id, data_point_id, data_point, field_name, value, submitted_at)
                            VALUES
                            (:version_name, :devco_id, :data_point_id, :data_point, :field_name, :value, :submitted_at)
                            ON CONFLICT(devco_id, data_point_id, field_name)
                            DO UPDATE SET value = excluded.value, submitted_at = excluded.submitted_at
                            """),
                            {
                                **entry,
                                "submitted_at": datetime.now().isoformat()
                            }
                        )
                st.success("All entries submitted successfully.")
            except Exception as e:
                st.error(f"Submission failed: {e}")