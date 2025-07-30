from sqlalchemy import create_engine, text
import os
import re

# Load DB
DB_PATH = os.path.join(os.path.dirname(__file__), "meinhardt.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

def get_devco_inputs(devco_id):
    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT field_name, value FROM devco_submissions
            WHERE devco_id = :devco_id
        """), {"devco_id": devco_id}).mappings().all()

    return {row["field_name"]: float(row["value"]) for row in result if row["value"] not in [None, ""]}

def parse_and_eval_formula(formula_code, field_values):
    try:
        # Replace `Label Name` with field_values["Label Name"]
        pattern = r"`([^`]+)`"
        processed_formula = re.sub(pattern, lambda m: f'field_values["{m.group(1)}"]', formula_code)
        return eval(processed_formula, {}, {"field_values": field_values})
    except Exception as e:
        print(f"Error evaluating formula: {formula_code}")
        print("Reason:", e)
        return None

def get_rating(score, thresholds):
    if score is None:
        return "Unable to evaluate"

    try:
        if eval(f"{score} {thresholds['good']}"):
            return "Good"
        elif eval(f"{score} {thresholds['satisfactory']}"):
            return "Satisfactory"
        elif eval(f"{score} {thresholds['needs_improvement']}"):
            return "Needs Improvement"
        else:
            return "Unknown"
    except Exception as e:
        return f"Threshold error: {e}"

def analyze_main_ag(devco_id):
    inputs = get_devco_inputs(devco_id)
    
    # Build a mapping of field_name → value (e.g., 'Forecast Budget': 1150000)
    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT field_name, value FROM devco_submissions
            WHERE devco_id = :devco_id
        """), {"devco_id": devco_id}).mappings().all()
    readable_inputs = {row["field_name"]: float(row["value"]) for row in result if row["value"] not in [None, ""]}

    with engine.begin() as conn:
        rows = conn.execute(text("SELECT * FROM main_ag_matrix")).mappings().fetchall()

    results = []
    for row in rows:
        formula = row["formula_alias"]
        score = parse_and_eval_formula(formula, readable_inputs)

        thresholds = {
            "good": row["threshold_good"],
            "satisfactory": row["threshold_satisfactory"],
            "needs_improvement": row["threshold_needs_improvement"]
        }

        rating = get_rating(score, thresholds)
        results.append({
            "criteria_id": row["criteria_id"],
            "score": score,
            "rating": rating
        })

    return results

if __name__ == "__main__":
    output = analyze_main_ag(devco_id="demo_devco_01")
    for row in output:
        print(row)