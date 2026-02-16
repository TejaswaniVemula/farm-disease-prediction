import pandas as pd

RISK_SCORE = {"Low": 1, "Mid": 2, "Medium": 2, "High": 3}

def load_risk_maps(disease_csv: str, symptom_csv: str):
    ddf = pd.read_csv(disease_csv)
    sdf = pd.read_csv(symptom_csv)
    disease_map = dict(zip(ddf["Disease"].astype(str), ddf["Risk_Level"].astype(str)))
    symptom_map = dict(zip(sdf["Symptom"].astype(str), sdf["Risk_Level"].astype(str)))
    return disease_map, symptom_map

def _norm(label: str) -> str:
    if not label:
        return "Low"
    label = str(label).strip().title()
    return "Medium" if label == "Mid" else label

def calculate_risk(predicted_disease: str, symptoms: list, confidence: float,
                   disease_risk_map: dict, symptom_risk_map: dict) -> dict:
    d_risk = _norm(disease_risk_map.get(predicted_disease, "Low"))
    d_score = RISK_SCORE.get(d_risk, 1)

    symptom_scores = []
    symptom_levels = []
    for s in symptoms:
        r = _norm(symptom_risk_map.get(s, "Low"))
        symptom_levels.append((s, r))
        symptom_scores.append(RISK_SCORE.get(r, 1))
    s_score = max(symptom_scores) if symptom_scores else 1

    if confidence >= 0.85:
        c_score = 3
    elif confidence >= 0.60:
        c_score = 2
    else:
        c_score = 1

    final = (0.45 * d_score) + (0.40 * s_score) + (0.15 * c_score)
    overall = "High" if final >= 2.6 else ("Medium" if final >= 1.8 else "Low")

    risky = [s for s, r in symptom_levels if RISK_SCORE.get(r, 1) == 3]
    explanation = "High-risk symptoms present: " + ", ".join(risky) if risky else "No high-risk symptoms detected."

    return {"overall_risk": overall, "explanation": explanation}
