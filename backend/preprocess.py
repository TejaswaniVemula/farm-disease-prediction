import re
import json
import pandas as pd
from typing import List, Dict, Union

VALID_ANIMALS = {"Cow", "Buffalo", "Goat", "Sheep"}

def normalize_text(s: str) -> str:
    s = str(s).replace("’", "'").strip()
    s = re.sub(r"\s+", " ", s)
    return s

def load_allowed_symptoms(path: str) -> List[str]:
    df = pd.read_csv(path)
    col = "Symptom" if "Symptom" in df.columns else df.columns[0]
    return sorted(set(df[col].dropna().astype(str).map(normalize_text)), key=str.lower)

def load_i18n(i18n_path: str) -> Dict:
    with open(i18n_path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_reverse_map(en_to_te: Dict[str, str]) -> Dict[str, str]:
    te_to_en = {}
    for en, te in en_to_te.items():
        if te:
            te_to_en[normalize_text(te)] = normalize_text(en)
    return te_to_en

def to_english_symptom(symptom: str, allowed_map: Dict[str, str], te_to_en: Dict[str, str]):
    s = normalize_text(symptom)
    if not s:
        return None
    if s in te_to_en:
        s = te_to_en[s]
    return allowed_map.get(s.lower(), None)

def preprocess_user_input(
    animal: str,
    symptoms_input: Union[str, List[str]],
    allowed_symptoms: List[str],
    i18n: Dict,
    min_symptoms: int = 3,
    max_symptoms: int = 8,
) -> Dict:
    errors = []

    animal_clean = normalize_text(animal).title()
    if animal_clean not in VALID_ANIMALS:
        te_animals = i18n.get("animals", {})
        rev_animals = {normalize_text(v): k for k, v in te_animals.items()}
        if normalize_text(animal) in rev_animals:
            animal_clean = rev_animals[normalize_text(animal)]
        else:
            errors.append(f"Invalid animal '{animal}'. Allowed: {sorted(VALID_ANIMALS)}")

    if isinstance(symptoms_input, list):
        raw = [normalize_text(x) for x in symptoms_input if str(x).strip()]
    else:
        raw = [normalize_text(x) for x in str(symptoms_input).split(",") if str(x).strip()]

    seen = set()
    raw_unique = []
    for x in raw:
        if x and x not in seen:
            seen.add(x)
            raw_unique.append(x)

    if len(raw_unique) > max_symptoms:
        raw_unique = raw_unique[:max_symptoms]

    allowed_map = {s.lower(): s for s in allowed_symptoms}
    en_to_te = i18n.get("symptoms", {})
    te_to_en = build_reverse_map(en_to_te)

    cleaned, unknown = [], []
    for s in raw_unique:
        english = to_english_symptom(s, allowed_map, te_to_en)
        if english:
            cleaned.append(english)
        else:
            unknown.append(s)

    cleaned2, seen2 = [], set()
    for x in cleaned:
        if x not in seen2:
            seen2.add(x)
            cleaned2.append(x)
    cleaned = cleaned2

    if len(cleaned) < min_symptoms:
        errors.append(f"Please provide at least {min_symptoms} valid symptoms.")
    if unknown:
        errors.append("Unknown symptoms: " + ", ".join(unknown))

    symptoms_csv = ", ".join(cleaned)
    symptoms_text = symptoms_csv.replace(",", " ")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "animal_en": animal_clean,
        "symptoms_en": cleaned,
        "symptoms_csv_en": symptoms_csv,
        "symptoms_text_en": symptoms_text,
    }
