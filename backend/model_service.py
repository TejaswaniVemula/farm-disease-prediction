# backend/model_service.py
from __future__ import annotations

import joblib
import numpy as np
from scipy.sparse import csr_matrix, hstack


class PredictorService:
    """
    Loads your persisted artifacts and returns top-k disease predictions.

    IMPORTANT:
    - The environment where you DEPLOY must have the same major dependencies
      used while training (especially scikit-learn & catboost).
    """

    def __init__(self, model_path: str, tfidf_path: str, animal_enc_path: str, disease_enc_path: str):
        try:
            self.model = joblib.load(model_path)
            self.tfidf = joblib.load(tfidf_path)
            self.animal_enc = joblib.load(animal_enc_path)
            self.disease_enc = joblib.load(disease_enc_path)
        except Exception as e:
            raise RuntimeError(
                "Failed to load model artifacts. Check paths and dependency versions.\n"
                f"Error: {e}"
            )

        # sanity: VotingClassifier should support predict_proba
        if not hasattr(self.model, "predict_proba"):
            raise RuntimeError("Loaded model does not support predict_proba().")

    def _build_feature_row(self, animal: str, symptoms_text: str):
        # TF-IDF (sparse)
        X_sym = self.tfidf.transform([symptoms_text])

        # Animal feature (sparse 1x1)
        animal_encoded = int(self.animal_enc.transform([animal])[0])
        X_animal = csr_matrix([[animal_encoded]])

        # Combine -> csr
        X = hstack([X_sym, X_animal], format="csr")

        # CatBoost sometimes fails on read-only sparse buffers in some environments.
        # This makes a safe, writeable copy.
        X = X.copy()

        return X

    def predict_topk(self, animal: str, symptoms_text: str, k: int = 3):
        if k < 1:
            k = 1

        X = self._build_feature_row(animal, symptoms_text)

        try:
            proba = self.model.predict_proba(X)[0]
        except ModuleNotFoundError as e:
            # Common when you trained with CatBoost but didn't install it in deploy.
            if "catboost" in str(e).lower():
                raise RuntimeError(
                    "CatBoost is missing in the deployment environment.\n"
                    "Install it or retrain without CatBoost and re-save artifacts."
                )
            raise
        except Exception as e:
            raise RuntimeError(f"Prediction failed: {e}")

        proba = np.asarray(proba, dtype=float)
        k = min(k, proba.size)

        top_idx = np.argsort(proba)[-k:][::-1]
        results = []
        for i in top_idx:
            results.append(
                {
                    "disease": str(self.disease_enc.classes_[i]),
                    "probability": float(proba[i]),
                }
            )
        return results
