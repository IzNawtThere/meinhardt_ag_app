import streamlit as st
import pandas as pd
from sqlalchemy import text
from db import engine


def render(username):
    st.header("Analyze AG - Assessment View")

    devco_id = username.split("@")[0] if "@" in username else username

    with engine.begin() as conn:
        # Get all relevant inputs
        raw_submissions = pd.read_sql(
            text("SELECT data_point_id, field_name, value FROM devco_submissions WHERE devco_id = :devco_id"),
            conn,
            params={"devco_id": devco_id}
        )
        # Get assessment matrix
        matrix = pd.read_sql(text("SELECT * FROM assessment_matrix"), conn)

    if raw_submissions.empty:
        st.warning("No submissions found for this DevCo.")
        return

    st.subheader("=== CLEANED DEVCO INPUTS ===")

    flat_inputs = {}
    for _, row in raw_submissions.iterrows():
        field = row["field_name"]
        val = row["value"]
        try:
            flat_inputs[field] = float(val)
        except:
            flat_inputs[field] = val

    st.json(flat_inputs)

    import re

    import re

    # Step A: Build alias map
    alias_map = {}
    for key in flat_inputs:
        alias = re.sub(r"[^\w]", "_", key.strip()).lower()
        alias_map[key] = alias

    # Step B: Assign values to each alias variable
    for original, alias in alias_map.items():
        try:
            exec(f"{alias} = float(flat_inputs[original])")
        except:
            exec(f"{alias} = 0")  # Default to 0 if conversion fails

    import re

    results = [] 

    for _, row in matrix.iterrows():
        criteria = row["assessment_criteria"]
        formula = row["formula"]
        weight = row["weightage"]

        st.markdown(f"**Evaluating Formula for:** `{criteria}`")
        st.markdown(f"→ Raw formula: `{formula}`")

        try:
            # STEP 1: Clean formula (remove non-breaking spaces, smart quotes, etc.)
            cleaned_formula = formula.replace('\xa0', ' ')  # U+00A0 non-breaking space
            cleaned_formula = re.sub(r'[“”]', '"', cleaned_formula)
            cleaned_formula = re.sub(r"[‘’]", "'", cleaned_formula)

            # STEP 2: Replace field names with their alias versions
            replaced_formula = cleaned_formula
            for original, alias in alias_map.items():
                replaced_formula = replaced_formula.replace(original, alias)

            st.markdown(f"→ Replaced with values: `{replaced_formula}`")

            # STEP 3: Eval
            result = eval(replaced_formula)
            st.success(f" Result = {result}")

            results.append({
                "assessment_criteria": criteria,
                "score": result,
                "weightage": weight
            })

        except Exception as e:
            st.error(f" Failed to evaluate: {e}")
            results.append({
                "assessment_criteria": criteria,
                "score": None,
                "weightage": weight,
                "error": str(e)
            })

    st.subheader("Final Computed Scores")
    st.dataframe(pd.DataFrame(results), use_container_width=True)