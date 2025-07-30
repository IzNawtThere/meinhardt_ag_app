import streamlit as st
import pandas as pd
from sqlalchemy import text
from db import engine
import re

st.set_page_config(page_title="Main AG Processor", layout="wide")

def extract_data_point_labels(formula):
    # Extract all text tokens assumed to be labels from the natural formula
    return re.findall(r"\b[A-Za-z0-9\s\(\)./-]+\b", formula)

def is_valid_math_expression(expr: str) -> bool:
    # Valid if only numbers, operators, and parentheses remain
    return bool(re.fullmatch(r"[\d+\-*/().\s]+", expr))

def generate_eval_formula(formula: str, inputs: dict) -> str:
    # Sort labels longest-first to prevent substring clashes
    for label in sorted(inputs.keys(), key=lambda x: -len(x)):
        # Escape regex-sensitive characters in label
        safe_label = re.escape(label)
        formula = re.sub(safe_label, str(inputs[label]), formula)
    return formula

def main():
    st.title("Main AG Processor 2.0")
    st.markdown("Evaluate all Main AG criteria based on real user input.")

    # Fetch all criteria from DB
    with engine.begin() as conn:
        all_criteria_df = pd.read_sql("SELECT * FROM main_ag_matrix", conn)

        # Dropdown filter
        pillars = sorted(all_criteria_df["pillar"].dropna().unique())
        selected_pillar = st.selectbox("Select Pillar to View Criteria", ["All"] + pillars)

        # Filter if not "All"
        if selected_pillar != "All":
            matrix_df = all_criteria_df[all_criteria_df["pillar"] == selected_pillar]
        else:
            matrix_df = all_criteria_df

    user_inputs = {}
    results = []

    st.subheader("Fill in required values")
    for _, row in matrix_df.iterrows():
        st.markdown(f"### {row['assessment_criteria']}")

        label_pairs = row["data_points_used"].split(";")
        local_inputs = {}

        for code in label_pairs:
            code = code.strip()
            if not code:
                continue

            # Get corresponding label
            with engine.begin() as conn:
                result = conn.execute(
                    text("SELECT field_name FROM data_point_labels WHERE data_point_id = :code"),
                    {"code": code}
                ).fetchone()

            if not result:
                st.warning(f"Missing label for data_point_id: {code}")
                continue

            label = result[0]
            input_type = row.get("input_type", "numeric").strip().lower()
            input_key = f"{row['assessment_criteria_id']}_{code}"

            if input_type == "categorical":
                try:
                    logic = eval(row.get("rating_logic", "{}"))
                    if not isinstance(logic, dict):
                        raise ValueError("Invalid rating logic format")

                    user_val = st.selectbox(
                        f"{label} ({code})",
                        options=list(logic.keys()),
                        key=input_key
                    )

                    user_inputs[label] = user_val
                    local_inputs[label] = user_val

                    # Store mapped rating directly
                    results.append({
                        "Criteria": row["assessment_criteria"],
                        "Formula": "Categorical",
                        "Score": user_val,
                        "Rating": logic.get(user_val, "Not Rated"),
                        "Weight": row["weightage"]
                    })

                    # Skip formula eval for categorical
                    continue

                except Exception as e:
                    st.error(f"Invalid rating logic for {label}: {e}")
                    continue

            else:
                user_val = st.number_input(f"{label} ({code})", key=input_key)

            user_inputs[label] = user_val
            local_inputs[label] = user_val

        # Attempt evaluation
        try:
            raw_formula = row["formula"]
            with st.expander("Debug Info"):
                st.markdown("**Formula Before Replacement:**")
                st.code(raw_formula, language="text")

                st.markdown("**Local Inputs Used:**")
                st.json(local_inputs)

                formula = generate_eval_formula(raw_formula, local_inputs)
                st.markdown("**Final Formula for Eval:**")
                st.code(formula, language="python")

                if re.search(r"/\s*0(\.0+)?", formula):
                    raise ZeroDivisionError("Division by zero")
                
                if not is_valid_math_expression(formula):
                    raise ValueError("Formula is not a valid mathematical expression")

            # Warn if missing required labels
            required_labels = extract_data_point_labels(raw_formula)
            missing_labels = [label for label in required_labels if label not in local_inputs]

            if missing_labels:
                st.warning(f"Missing values for: {', '.join(missing_labels)}")

            score = eval(formula)

            if score >= row["threshold_good"]:
                rating = "Good"
            elif score >= row["threshold_satisfactory"]:
                rating = "Satisfactory"
            elif score >= row["threshold_needs_improvement"]:
                rating = "Needs Improvement"
            else:
                rating = "Below Threshold"

            results.append({
                "Criteria": row["assessment_criteria"],
                "Formula": formula,
                "Score": round(score, 4) if isinstance(score, (int, float)) else score,
                "Rating": rating,
                "Weight": row["weightage"]
            })

        except ZeroDivisionError:
            results.append({
                "Criteria": row["assessment_criteria"],
                "Formula": "Division by zero",
                "Score": "Error",
                "Rating": "Error",
                "Weight": row["weightage"]
            })

        except Exception as e:
            results.append({
                "Criteria": row["assessment_criteria"],
                "Formula": str(e),
                "Score": "Error",
                "Rating": "Error",
                "Weight": row["weightage"]
            })

    # Show table
    st.subheader("Evaluation Results")
    results_df = pd.DataFrame(results)
    st.dataframe(results_df)

    try:
        valid_scores = results_df[results_df["Score"] != "Error"]
        valid_scores["Weighted"] = valid_scores["Score"] * valid_scores["Weight"]
        final_score = valid_scores["Weighted"].sum()
        st.metric("Final Weighted Score", round(final_score, 4))
    except:
        st.warning("Could not compute weighted score due to errors.")

if __name__ == "__main__":
    main()
