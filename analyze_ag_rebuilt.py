import streamlit as st
import pandas as pd
from sqlalchemy import text
from db import engine
import re

from difflib import get_close_matches

def normalize_label(label: str):
    return (
        label.lower()
        .replace("no.", "")
        .replace("number", "")
        .replace("of", "")
        .replace("(", "")
        .replace(")", "")
        .replace(".", "")
        .replace(",", "")
        .replace("-", "_")
        .replace("/", "_")
        .replace("&", "and")
        .replace(" ", "_")
        .strip("_")
    )

def extract_variable_map(data_points_used):
    """
    Parses 'data_points_used' like:
    'Planned Value (PV); Earned Value (EV)' OR
    'No. of planned milestones (No.)'
    Returns a dict: {'Planned Value': 'pv', 'No. of planned milestones': 'planned_milestones'}
    """
    var_map = {}
    if pd.isna(data_points_used):
        return var_map

    for part in data_points_used.split(";"):
        part = part.strip()
        match = re.match(r"(.+?)\s*\(([^)]+)\)", part)
        if match:
            label, short_code = match.groups()
            code = normalize_label(short_code)
            var_map[label.strip()] = code
        else:
            # fallback: no code provided, normalize full label
            var_map[part.strip()] = normalize_label(part.strip())

    return var_map

def match_variable_to_input(var_string, flat_inputs):
    """
    Given a variable from a formula, try to fuzzy-match it
    to an available key in flat_inputs.
    """
    candidates = get_close_matches(var_string, flat_inputs.keys(), n=1, cutoff=0.6)
    return candidates[0] if candidates else None

def check_threshold(score, threshold_string):
    if pd.isna(threshold_string) or not str(threshold_string).strip():
        return False
    
    threshold_string = str(threshold_string).strip()
    
    # Handle percentage signs
    threshold_string = threshold_string.replace("%", "")

    try:
        # Range like "30-70"
        if "-" in threshold_string:
            lower, upper = map(float, threshold_string.split("-"))
            return lower <= score <= upper
        elif threshold_string.startswith(">="):
            return score >= float(threshold_string[2:])
        elif threshold_string.startswith(">"):
            return score > float(threshold_string[1:])
        elif threshold_string.startswith("<="):
            return score <= float(threshold_string[2:])
        elif threshold_string.startswith("<"):
            return score < float(threshold_string[1:])
        elif threshold_string.startswith("="):
            return score == float(threshold_string[1:])
        else:
            return score >= float(threshold_string)
    except:
        return False

def render(username):
    st.header("Analyze DevCo Assessment")

    devco_id = username.split("@")[0] if "@" in username else username

    # Load inputs
    with engine.begin() as conn:
        df_inputs = pd.read_sql(text("""
            SELECT data_point, value
            FROM devco_submissions
            WHERE devco_id = :devco_id AND field_name = 'input_value'
        """), conn, params={"devco_id": devco_id})

        df_matrix = pd.read_sql(text("SELECT * FROM assessment_matrix"), conn)

    # Clean inputs into dict
    flat_inputs = {}
    for _, row in df_inputs.iterrows():
        data_point_label = row["data_point"]
        val = row["value"]
        
        try:
            val = float(val)
        except:
            val = None

        # Normalize full label
        full_key = normalize_label(data_point_label)
        flat_inputs[full_key] = val

        # Extract short code if available (e.g., from "(PV)")
        match = re.match(r".+?\(([^)]+)\)", data_point_label)
        if match:
            short_code = normalize_label(match.group(1))
            flat_inputs[short_code] = val

    with st.expander("View Cleaned DevCo Inputs", expanded=False):
        styled_inputs = pd.DataFrame([
            {"Data Point": k, "Value": v if v is not None else "NULL"}
            for k, v in flat_inputs.items()
        ])
        st.dataframe(styled_inputs, use_container_width=True)

    st.subheader("Formula Evaluation Results")

    results = []

    for _, row in df_matrix.iterrows():
        criteria = row["assessment_criteria"]
        raw_formula = str(row["formula"]).replace("\u00A0", " ").strip()
        weight = row.get("weightage", 1)

        st.markdown(f"---\n**Criteria:** `{criteria}`")

        # Build variable map for this formula
        var_map = extract_variable_map(row.get("data_points_used", ""))

        try:
            # Step 1: Identify which data points are referenced
            # Extract words likely to be variables (split by "/", "(", etc)
            # Identify all alphanumeric tokens that could be variable names
            used_vars = []
            
            # Apply variable mapping correctly
            for verbose_label, code in var_map.items():
                # Use regex to replace only full matches
                escaped_label = re.escape(verbose_label)
                pattern = rf"\b{escaped_label}\b"
                if re.search(pattern, raw_formula):
                    raw_formula = re.sub(pattern, code, raw_formula)
                    used_vars.append((verbose_label, code))

            eval_formula = raw_formula

            # --- INSERT STARTS HERE ---
            # Additionally replace (EV), (PV) etc. in the formula
            for verbose_label, code in used_vars:
                match = re.search(r"\(([^)]+)\)", verbose_label)
                if match:
                    alt_code = normalize_label(match.group(1))
                    if alt_code in flat_inputs:
                        eval_formula = eval_formula.replace(match.group(1), alt_code)
            # --- INSERT ENDS HERE ---

            st.write("Detected Variables:", used_vars)

            # Step 2: Replace variable codes with actual values
            for _, code in used_vars:
                val = flat_inputs.get(code)
                if val is None:
                    raise ValueError(f"Missing input for: {code}")
                eval_formula = eval_formula.replace(code, str(val))

            st.code(eval_formula, language='python')

            # Step 3: Evaluate the formula
            try:
                # Only allow math functions
                # Check for non-numeric variables
                non_numeric_vars = [code for _, code in used_vars if not isinstance(flat_inputs.get(code), (int, float))]
                if non_numeric_vars:
                    raise ValueError(f"Non-numeric inputs found for variables: {non_numeric_vars}")
                import math
                allowed_names = {k: getattr(math, k) for k in dir(math) if not k.startswith("__")}
                score = eval(eval_formula, {"__builtins__": {}}, allowed_names)
            except Exception as eval_err:
                raise ValueError(f"Formula evaluation failed: {eval_err}")

            # Step 4: Assign a rating based on thresholds
            rating = "Undefined"
            try:
                threshold_good = row.get("thresholds_good")
                threshold_satisfactory = row.get("thresholds_satisfactory")
                threshold_needs = row.get("thresholds_needs_improvement")

                if check_threshold(score, row.get("thresholds_good")):
                    rating = "Good"
                elif check_threshold(score, row.get("thresholds_satisfactory")):
                    rating = "Satisfactory"
                elif check_threshold(score, row.get("thresholds_needs_improvement")):
                    rating = "Needs Improvement"

            except Exception as rating_err:
                st.warning(f"Rating error: {rating_err}")

            st.success(f"Score: {score} → **Rating: {rating}**")

            results.append({
                "criteria": criteria,
                "score": score,
                "weight": weight,
                "rating": rating
            })

        except Exception as e:
            st.error(f"Error: {e}")
            results.append({
                "criteria": criteria,
                "score": None,
                "weight": weight,
                "error": str(e)
            })

