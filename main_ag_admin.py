import streamlit as st
import pandas as pd
from sqlalchemy import text
from db import engine

def main_ag_admin():
    st.title("Main AG Admin Panel")
    st.markdown("Use this panel to add, edit, or remove Main AG criteria dynamically.")

    # Fetch current matrix
    with engine.begin() as conn:
        df = pd.read_sql("SELECT * FROM main_ag_matrix", conn)

    st.subheader("Current Criteria")
    st.dataframe(df)

    st.subheader("Add New Criteria")
    with st.form("add_criteria"):
        criteria_id = st.text_input("Criteria ID", placeholder="E.g. CEO-AC-004")
        criteria_name = st.text_input("Criteria Name", placeholder="Short description")
        data_points_used = st.text_input("Data Points Used", placeholder="E.g. CEO-DP-001;CEO-DP-002")
        formula_natural = st.text_area("Natural Language Formula")
        formula_code = st.text_area("Code Formula", placeholder="E.g. (CEO_DP_002 - CEO_DP_001) / CEO_DP_001")
        weightage = st.number_input("Weightage", min_value=0.0, max_value=1.0, step=0.1)
        threshold_good = st.number_input("Threshold: Good", step=0.01)
        threshold_satisfactory = st.number_input("Threshold: Satisfactory", step=0.01)
        threshold_needs_improvement = st.number_input("Threshold: Needs Improvement", step=0.01)
        formula_alias = st.text_area("Formula Alias (Optional)")

        submitted = st.form_submit_button("Submit")
        if submitted:
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO main_ag_matrix (
                        criteria_id, criteria_name, data_points_used, formula_natural,
                        formula_code, weightage, threshold_good, threshold_satisfactory,
                        threshold_needs_improvement, formula_alias
                    ) VALUES (
                        :criteria_id, :criteria_name, :data_points_used, :formula_natural,
                        :formula_code, :weightage, :threshold_good, :threshold_satisfactory,
                        :threshold_needs_improvement, :formula_alias
                    )
                """), {
                    "criteria_id": criteria_id,
                    "criteria_name": criteria_name,
                    "data_points_used": data_points_used,
                    "formula_natural": formula_natural,
                    "formula_code": formula_code,
                    "weightage": weightage,
                    "threshold_good": threshold_good,
                    "threshold_satisfactory": threshold_satisfactory,
                    "threshold_needs_improvement": threshold_needs_improvement,
                    "formula_alias": formula_alias
                })
            st.success("New assessment criterion added successfully!")