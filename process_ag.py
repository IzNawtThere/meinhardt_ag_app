import streamlit as st
import pandas as pd
from db import engine
from sqlalchemy import text

def render(username):
    st.header("Main AG Processor")

    devco_id = username.split("@")[0] if "@" in username else username

    with engine.begin() as conn:
        ag_df = pd.read_sql("SELECT * FROM pilot_ag_master", conn)

        submission_df = pd.read_sql(
            text("""
                SELECT data_point_id, field_name, value
                FROM devco_submissions
                WHERE devco_id = :devco_id
            """),
            conn,
            params={"devco_id": devco_id}
        )

    st.write("DevCo Submissions Raw:")
    st.dataframe

    submission_pivot = submission_df.pivot_table(
        index="data_point_id", 
        columns="field_name",
        values="value",
        aggfunc="first"
    ).reset_index()

    st.write("Pivoted DevCo Submission (input value / remarks):")
    st.dataframe(submission_pivot)

    merged_df = ag_df.merge(submission_pivot, on="data_point_id", how="left")

    if "input_value" not in merged_df.columns:
        merged_df["input_value"] = None

    merged_df["input_value"] = pd.to_numeric(merged_df["input_value"], errors="coerce")

    st.subheader("Merged View: Master AG + DevCo Inputs")
    st.dataframe(merged_df, use_container_width=True)

    merged_df["completion_score"] = merged_df["input_value"].fillna(0) / 100
    merged_df["flag_needs_attention"] = merged_df["completion_score"] < 0.7

    st.subheader("Processed AG Outputs")
    st.dataframe(
        merged_df[["data_point_id", "data_point", "input_value", "completion_score", "flag_needs_attention"]],
        use_container_width=True
    )

    st.success("AG Processing Complete.")