# backend/main.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from preprocess import load_allowed_symptoms, preprocess_user_input, load_i18n
from model_service import PredictorService
from risk import load_risk_maps, calculate_risk


# -----------------------------
# App
# -----------------------------
app = FastAPI(title="Farm Animal Disease Prediction API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Paths (ONLY Path objects)
# Repo layout:
#   project_root/
#     artifacts/
#     backend/
#       main.py
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent          # .../backend
ART_DIR = BASE_DIR.parent / "artifacts"             # .../artifacts

MODEL_PATH = ART_DIR / "hybrid_model.pkl"
TFIDF_PATH = ART_DIR / "tfidf.pkl"
ANIMAL_ENC_PATH = ART_DIR / "animal_encoder.pkl"
DISEASE_ENC_PATH = ART_DIR / "disease_encoder.pkl"

SYMPTOMS_CSV = ART_DIR / "unique_symptoms.csv"
DISEASE_RISK_CSV = ART_DIR / "disease_risk_levels.csv"
SYMPTOM_RISK_CSV = ART_DIR / "symptom_risk_levels.csv"
I18N_JSON = ART_DIR / "i18n_te.json"


# -----------------------------
# Globals loaded at startup
# -----------------------------
i18n: Dict[str, Any] = {}
allowed_symptoms: List[str] = []
predictor: Optional[PredictorService] = None
disease_risk_map: Dict[str, str] = {}
symptom_risk_map: Dict[str, str] = {}


# -----------------------------
# Helpers (these were missing!)
# -----------------------------
def bi(text_en: str, section: str) -> Dict[str, str]:
    te = i18n.get(section, {}).get(text_en, "—")
    return {"en": text_en, "te": te, "display": f"{text_en} / {te}"}


def bi_risk_phrase(level_en: str) -> Dict[str, str]:
    phrase_en = f"{level_en} Risk"
    phrase_te = i18n.get("risk_phrase", {}).get(phrase_en, "—")
    return {"en": phrase_en, "te": phrase_te, "display": f"{phrase_en} / {phrase_te}"}


def ensure_loaded() -> None:
    """Raise 503 if artifacts weren't loaded."""
    if predictor is None or not allowed_symptoms or not i18n:
        raise HTTPException(
            status_code=503,
            detail="Service not ready (artifacts not loaded). Check /health for details.",
        )


# -----------------------------
# Startup
# -----------------------------
@app.on_event("startup")
def load_everything() -> None:
    global i18n, allowed_symptoms, predictor, disease_risk_map, symptom_risk_map

    required = [
        MODEL_PATH, TFIDF_PATH, ANIMAL_ENC_PATH, DISEASE_ENC_PATH,
        SYMPTOMS_CSV, DISEASE_RISK_CSV, SYMPTOM_RISK_CSV, I18N_JSON,
    ]

    missing = [str(p) for p in required if not p.exists()]
    if missing:
        # Fail fast so you see the real reason in Render logs
        raise FileNotFoundError("Missing artifacts:\n" + "\n".join(missing))

    i18n = load_i18n(str(I18N_JSON))
    allowed_symptoms = load_allowed_symptoms(str(SYMPTOMS_CSV))

    predictor = PredictorService(
        str(MODEL_PATH),
        str(TFIDF_PATH),
        str(ANIMAL_ENC_PATH),
        str(DISEASE_ENC_PATH),
    )

    disease_risk_map, symptom_risk_map = load_risk_maps(
        str(DISEASE_RISK_CSV),
        str(SYMPTOM_RISK_CSV),
    )


# -----------------------------
# Schemas
# -----------------------------
class PredictRequest(BaseModel):
    animal: str = Field(..., examples=["Cow"])
    symptoms: List[str] = Field(
        ..., min_items=3, examples=[["High fever", "Nasal discharge", "Cough"]]
    )
    top_k: int = Field(3, ge=1, le=5)


class PredictResponse(BaseModel):
    animal: dict
    symptoms: List[dict]
    predictions: List[dict]
    risk: dict
    prevention: Optional[dict] = None
    precautions: Optional[dict] = None


# -----------------------------
# Routes
# -----------------------------
@app.get("/")
def root():
    return {"status": "ok", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health():
    required = [
        MODEL_PATH, TFIDF_PATH, ANIMAL_ENC_PATH, DISEASE_ENC_PATH,
        SYMPTOMS_CSV, DISEASE_RISK_CSV, SYMPTOM_RISK_CSV, I18N_JSON,
    ]
    missing = [str(p) for p in required if not p.exists()]

    return {
        "status": "ok" if not missing and predictor is not None else "not_ready",
        "artifacts_dir": str(ART_DIR),
        "missing_artifacts": missing,
        "symptoms_count": len(allowed_symptoms),
        "i18n_loaded": bool(i18n),
        "predictor_loaded": predictor is not None,
    }


@app.get("/symptoms")
def get_symptoms():
    ensure_loaded()
    return {"symptoms": [bi(s, "symptoms") for s in allowed_symptoms]}


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    ensure_loaded()
    assert predictor is not None  # for type-checkers

    prep = preprocess_user_input(req.animal, req.symptoms, allowed_symptoms, i18n)

    if not prep["ok"]:
        # Use 422 since input is invalid
        raise HTTPException(status_code=422, detail={"errors": prep["errors"]})

    preds = predictor.predict_topk(prep["animal_en"], prep["symptoms_text_en"], k=req.top_k)
    top1 = preds[0]

    risk_raw = calculate_risk(
        predicted_disease=top1["disease"],
        symptoms=prep["symptoms_en"],
        confidence=top1["probability"],
        disease_risk_map=disease_risk_map,
        symptom_risk_map=symptom_risk_map,
    )
    risk_bi = bi_risk_phrase(risk_raw["overall_risk"])

    pp = i18n.get("prevention_precautions", {}).get(top1["disease"])
    prevention = precautions = None

    if pp:
        prevention = {
            "en": pp.get("prevention_en", ""),
            "te": pp.get("prevention_te", ""),
            "display": f"{pp.get('prevention_en','')} / {pp.get('prevention_te','')}",
        }
        precautions = {
            "en": pp.get("precaution_en", ""),
            "te": pp.get("precaution_te", ""),
            "display": f"{pp.get('precaution_en','')} / {pp.get('precaution_te','')}",
        }

    return {
        "animal": bi(prep["animal_en"], "animals"),
        "symptoms": [bi(s, "symptoms") for s in prep["symptoms_en"]],
        "predictions": [
            {
                "disease": bi(p["disease"], "diseases"),
                "probability": p["probability"],
                "probability_percent": round(p["probability"] * 100, 2),
            }
            for p in preds
        ],
        "risk": {"overall": risk_bi, "explanation": risk_raw.get("explanation", "")},
        "prevention": prevention,
        "precautions": precautions,
    }
