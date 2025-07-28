import streamlit as st
import pandas as pd
from db import engine

def render():
    st.header("Edit AG Structure (Add/Delete Data Points)")

    with engine.connect() as conn:
        ag_df = pd.read_sql("SELECT * FROM pilot_ag_master", conn)

    st.subheader("Current AG Table (Preview)")
    st.dataframe(ag_df, use_container_width=True)

    # ---------------- Add New ----------------
    st.subheader("Add a New Data Point")
    with st.form("add_dp_form"):
        new_dp_id = st.text_input("New Data Point ID", placeholder="e.g. PM-DP-99")
        new_dp_desc = st.text_input("Data Point Description")
        insert_at = st.number_input("Insert at Row Index (0-based)", min_value=0, max_value=len(ag_df), value=len(ag_df))
        submitted = st.form_submit_button("Add Data Point")

        if submitted:
            existing_ids = ag_df["data_point_id"].dropna().str.upper().values
            if new_dp_id.upper() in existing_ids:
                st.error(f"Data Point ID '{new_dp_id}' already exists. Choose a unique ID.")
            elif not new_dp_id or not new_dp_desc:
                st.warning("Both Data Point ID and Description are required.")
            else:
                new_row = pd.DataFrame([{
                    "data_point_id": new_dp_id.upper(),
                    "data_point": new_dp_desc
                }])
                top = ag_df.iloc[:insert_at]
                bottom = ag_df.iloc[insert_at:]
                updated_df = pd.concat([top, new_row, bottom], ignore_index=True)

                updated_df.to_sql("pilot_ag_master", engine, if_exists="replace", index=False)
                st.success(f"Added '{new_dp_id}' at position {insert_at}")
                st.rerun()

    # ---------------- Delete Existing ----------------
    st.subheader("Delete a Data Point")
    valid_ids = ag_df["data_point_id"].dropna().unique().tolist()
    if valid_ids:
        dp_to_delete = st.selectbox("Select Data Point ID to Delete", valid_ids)
        if st.button("Delete Selected Data Point"):
            updated_df = ag_df[ag_df["data_point_id"] != dp_to_delete].reset_index(drop=True)
            updated_df.to_sql("pilot_ag_master", engine, if_exists="replace", index=False)
            st.success(f"Deleted '{dp_to_delete}' from AG table")
            st.rerun()
    else:
        st.info("No data points available for deletion.")
