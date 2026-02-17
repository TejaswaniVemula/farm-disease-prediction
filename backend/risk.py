# backend/risk.py
from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Tuple

# Scores used in weighted risk formula
RISK_SCORE = {"Low": 1, "Medium": 2, "High": 3}


def _norm(label: str) -> str:
    """
    Normalize risk labels from CSV.
    Accepts: low/mid/medium/high, etc.
    """
    if not label:
        return "Low"
    x = str(label).strip().lower()

    if x in {"mid", "med", "medium"}:
        return "Medium"
    if x in {"high"}:
        return "High"
    return "Low"


def _read_two_col_csv(path: str, key_name: str, val_name: str) -> Dict[str, str]:
    """
    Reads CSV with headers and returns dict[key]=value.
    No pandas => easier deployment.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Risk CSV not found: {p}")

    with p.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header row: {p}")

        # allow flexible headers (case-insensitive)
        fields = {h.strip().lower(): h for h in reader.fieldnames}
        if key_name.lower() not in fields or val_name.lower() not in fields:
            raise ValueError(
                f"CSV must contain columns '{key_name}' and '{val_name}'. Found: {reader.fieldnames}"
            )

        key_col = fields[key_name.lower()]
        val_col = fields[val_name.lower()]

        out: Dict[str, str] = {}
        for row in reader:
            k = (row.get(key_col) or "").strip()
            v = (row.get(val_col) or "").strip()
            if k:
                out[k] = v
        return out


def load_risk_maps(disease_csv: str, symptom_csv: str):
    """
    Returns:
      disease_map: {Disease: Risk_Level}
      symptom_map: {Symptom: Risk_Level}
    """
    disease_map = _read_two_col_csv(disease_csv, "Disease", "Risk_Level")
    symptom_map = _read_two_col_csv(symptom_csv, "Symptom", "Risk_Level")
    return disease_map, symptom_map


def calculate_risk(
    predicted_disease: str,
    symptoms: List[str],
    confidence: float,
    disease_risk_map: Dict[str, str],
    symptom_risk_map: Dict[str, str],
) -> Dict[str, str]:
    """
    Hybrid risk:
      45% disease severity + 40% worst symptom severity + 15% model confidence
    """
    # disease risk
    d_level = _norm(disease_risk_map.get(predicted_disease, "Low"))
    d_score = RISK_SCORE[d_level]

    # symptom risk (use max severity symptom)
    symptom_levels: List[Tuple[str, str]] = []
    symptom_scores: List[int] = []

    for s in symptoms:
        lvl = _norm(symptom_risk_map.get(s, "Low"))
        symptom_levels.append((s, lvl))
        symptom_scores.append(RISK_SCORE[lvl])

    s_score = max(symptom_scores) if symptom_scores else 1

    # confidence risk bucket
    if confidence >= 0.85:
        c_score = 3
    elif confidence >= 0.60:
        c_score = 2
    else:
        c_score = 1

    final = (0.45 * d_score) + (0.40 * s_score) + (0.15 * c_score)

    overall = "High" if final >= 2.6 else ("Medium" if final >= 1.8 else "Low")

    risky_symptoms = [s for s, lvl in symptom_levels if lvl == "High"]
    explanation = (
        "High-risk symptoms present: " + ", ".join(risky_symptoms)
        if risky_symptoms
        else "No high-risk symptoms detected."
    )

    return {"overall_risk": overall, "explanation": explanation}
