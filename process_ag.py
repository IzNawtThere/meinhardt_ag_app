import streamlit as st
import pandas as pd
from sqlalchemy import text
from db import engine
from evaluate_main_ag import evaluate_main_ag

def render(username):
    st.header("Main AG Processor")

    st.markdown("""
        <style>
            h1, h2, h3 {
                color: #003366;
            }
            .stDataFrame, .stTable {
                border-radius: 8px;
                background-color: #f9f9f9;
            }
            section.main > div {
                padding: 2rem 3rem;
            }
        </style>
    """, unsafe_allow_html=True)

    devco_id = username.split("@")[0] if "@" in username else username

    st.markdown(f"### Processing for DevCo: `{devco_id}`")

    # Step 1: Fetch latest submissions from devco_submissions
    with engine.begin() as conn:
        submissions_df = pd.read_sql(text("""
            SELECT data_point_id, value
            FROM devco_submissions
            WHERE devco_id = :devco_id AND field_name = 'input_value'
        """), conn, params={"devco_id": devco_id})

        matrix_df = pd.read_sql("SELECT * FROM main_ag_matrix", conn)

    if submissions_df.empty or matrix_df.empty:
        st.warning("Missing DevCo submissions or Main AG matrix.")
        return

    # Display placeholders
    st.subheader("1. Raw Submissions")
    st.dataframe(submissions_df, use_container_width=True)

    st.subheader("2. Main AG Matrix")
    st.dataframe(matrix_df, use_container_width=True)

    st.info("Next step: Map codes to values, evaluate formulas, and compute ratings.")

    st.subheader("3. Evaluated Results")

    results_df = evaluate_main_ag(devco_id)
    st.dataframe(results_df, use_container_width=True)

    st.subheader("4. Filter by Rating")

    selected_ratings = st.multiselect(
        "Select Ratings to View",
        options=["Good", "Satisfactory", "Needs Improvement", "Unrated", "Threshold Error", "Error", "Invalid"],
        default=["Needs Improvement", "Satisfactory", "Good"]
    )

    filtered_df = results_df[results_df["Rating"].isin(selected_ratings)]
    st.dataframe(filtered_df, use_container_width=True)

    st.subheader("5. Rating Breakdown")

    breakdown = results_df["Rating"].value_counts().rename_axis("Rating").reset_index(name="Count")
    st.dataframe(breakdown)

    # Optional weighted score (only if scores are valid numbers)
    st.subheader("6. Weighted Score Summary")

    numeric_df = results_df[pd.to_numeric(results_df["Score"], errors="coerce").notna()].copy()
    numeric_df["Weighted Score"] = numeric_df["Score"] * numeric_df["Weight"]

    if not numeric_df.empty:
        total_weight = numeric_df["Weight"].sum()
        total_score = numeric_df["Weighted Score"].sum()
        avg_score = total_score / total_weight if total_weight > 0 else 0

        st.metric("Weighted Average Score", round(avg_score, 3))
    else:
        st.info("No valid numeric scores found to compute weighted average.")
        st.subheader("7. Download Results")

    selected_df = filtered_df if not filtered_df.empty else results_df

    @st.cache_data
    def convert_df_to_excel(df):
        from io import BytesIO
        import xlsxwriter

        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Results', index=False)
        processed_data = output.getvalue()
        return processed_data

    excel_data = convert_df_to_excel(selected_df)

    st.download_button(
        label="Download Results as Excel",
        data=excel_data,
        file_name=f"{devco_id}_AG_Results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

