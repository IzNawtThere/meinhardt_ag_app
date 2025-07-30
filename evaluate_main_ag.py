import pandas as pd
from sqlalchemy import text
from db import engine
import re

def evaluate_main_ag(devco_id: str) -> pd.DataFrame:
    with engine.begin() as conn:
        submissions_df = pd.read_sql(text("""
            SELECT data_point_id, value
            FROM devco_submissions
            WHERE devco_id = :devco_id AND field_name = 'input_value'
        """), conn, params={"devco_id": devco_id})

        matrix_df = pd.read_sql("SELECT * FROM main_ag_matrix", conn)

    if submissions_df.empty or matrix_df.empty:
        raise ValueError("Missing DevCo submissions or Main AG matrix.")

    flat_inputs = {
        row["data_point_id"]: float(row["value"])
        for _, row in submissions_df.iterrows()
        if row["value"] is not None and str(row["value"]).replace('.', '', 1).isdigit()
    }

    results = []

    for _, row in matrix_df.iterrows():
        formula = row["formula_code"]
        raw_formula = formula
        assessment_id = row["criteria_id"]
        criteria = row["criteria_name"]
        weight = row["weightage"]

        thresholds = {
            "good": row["threshold_good"],
            "satisfactory": row["threshold_satisfactory"],
            "needs_improvement": row["threshold_needs_improvement"]
        }

        used_vars = re.findall(r"[A-Z]+[-_]+DP[-_]+\d+", formula)
        missing = []

        for var in used_vars:
            norm_var = var.replace("_", "-")
            if norm_var in flat_inputs:
                formula = formula.replace(var, str(flat_inputs[norm_var]))
            else:
                missing.append(norm_var)

        try:
            if missing:
                raise ValueError(f"Missing values for: {', '.join(missing)}")
            score = eval(formula)
        except Exception as e:
            score = None
            rating = f"Error: {e}"
        else:
            try:
                if isinstance(score, str) or score is None:
                    rating = "Invalid"
                elif eval(f"{score} {thresholds['good']}"):
                    rating = "Good"
                elif eval(f"{score} {thresholds['satisfactory']}"):
                    rating = "Satisfactory"
                elif eval(f"{score} {thresholds['needs_improvement']}"):
                    rating = "Needs Improvement"
                else:
                    rating = "Unrated"
            except:
                rating = "Threshold Error"

        results.append({
            "Assessment ID": assessment_id,
            "Criteria": criteria,
            "Formula": raw_formula,
            "Evaluated Formula": formula,
            "Score": score,
            "Rating": rating,
            "Weight": weight,
        })

    return pd.DataFrame(results)