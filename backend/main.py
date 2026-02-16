from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional
import os
from fastapi.middleware.cors import CORSMiddleware
from preprocess import load_allowed_symptoms, preprocess_user_input, load_i18n
from model_service import PredictorService
from risk import load_risk_maps, calculate_risk

APP_DIR = os.path.dirname(os.path.abspath(__file__))
ART_DIR = os.path.join(APP_DIR, "..", "artifacts")

MODEL_PATH = os.path.join(ART_DIR, "hybrid_model.pkl")
TFIDF_PATH = os.path.join(ART_DIR, "tfidf.pkl")
ANIMAL_ENC_PATH = os.path.join(ART_DIR, "animal_encoder.pkl")
DISEASE_ENC_PATH = os.path.join(ART_DIR, "disease_encoder.pkl")

SYMPTOMS_CSV = os.path.join(ART_DIR, "unique_symptoms.csv")
DISEASE_RISK_CSV = os.path.join(ART_DIR, "disease_risk_levels.csv")
SYMPTOM_RISK_CSV = os.path.join(ART_DIR, "symptom_risk_levels.csv")
I18N_JSON = os.path.join(ART_DIR, "i18n_te.json")

app = FastAPI(title="Farm Animal Disease Prediction API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


i18n = load_i18n(I18N_JSON)
allowed_symptoms = load_allowed_symptoms(SYMPTOMS_CSV)
predictor = PredictorService(MODEL_PATH, TFIDF_PATH, ANIMAL_ENC_PATH, DISEASE_ENC_PATH)
disease_risk_map, symptom_risk_map = load_risk_maps(DISEASE_RISK_CSV, SYMPTOM_RISK_CSV)

def bi(text_en: str, section: str) -> dict:
    te = i18n.get(section, {}).get(text_en, "—")
    return {"en": text_en, "te": te, "display": f"{text_en} / {te}"}

def bi_risk_phrase(level_en: str) -> dict:
    phrase_en = f"{level_en} Risk"
    phrase_te = i18n.get("risk_phrase", {}).get(phrase_en, "—")
    return {"en": phrase_en, "te": phrase_te, "display": f"{phrase_en} / {phrase_te}"}

class PredictRequest(BaseModel):
    animal: str = Field(..., examples=["Cow"])
    symptoms: List[str] = Field(..., min_items=3, examples=[["High fever", "Nasal discharge", "Cough"]])
    top_k: int = Field(3, ge=1, le=5)

class PredictResponse(BaseModel):
    animal: dict
    symptoms: List[dict]
    predictions: List[dict]
    risk: dict
    prevention: Optional[dict] = None
    precautions: Optional[dict] = None

@app.get("/symptoms")
def get_symptoms():
    return {"symptoms": [bi(s, "symptoms") for s in allowed_symptoms]}

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    prep = preprocess_user_input(req.animal, req.symptoms, allowed_symptoms, i18n)

    if not prep["ok"]:
        return {
            "animal": {"en": req.animal, "te": "—", "display": f"{req.animal} / —"},
            "symptoms": [{"en": x, "te": "—", "display": f"{x} / —"} for x in req.symptoms],
            "predictions": [],
            "risk": {"overall": {"en": "N/A", "te": "—", "display": "N/A / —"}, "explanation": "; ".join(prep["errors"])},
            "prevention": None,
            "precautions": None
        }

    preds = predictor.predict_topk(prep["animal_en"], prep["symptoms_text_en"], k=req.top_k)
    top1 = preds[0]

    risk_raw = calculate_risk(top1["disease"], prep["symptoms_en"], top1["probability"], disease_risk_map, symptom_risk_map)
    risk_bi = bi_risk_phrase(risk_raw["overall_risk"])

    pp = i18n.get("prevention_precautions", {}).get(top1["disease"], None)
    prev = prec = None
    if pp:
        prev = {"en": pp.get("prevention_en",""), "te": pp.get("prevention_te",""),
                "display": f"{pp.get('prevention_en','')} / {pp.get('prevention_te','')}"}
        prec = {"en": pp.get("precaution_en",""), "te": pp.get("precaution_te",""),
                "display": f"{pp.get('precaution_en','')} / {pp.get('precaution_te','')}"}

    return {
        "animal": bi(prep["animal_en"], "animals"),
        "symptoms": [bi(s, "symptoms") for s in prep["symptoms_en"]],
        "predictions": [{"disease": bi(p["disease"], "diseases"),
                         "probability": p["probability"],
                         "probability_percent": round(p["probability"]*100, 2)} for p in preds],
        "risk": {"overall": risk_bi, "explanation": risk_raw.get("explanation","")},
        "prevention": prev,
        "precautions": prec
    }
