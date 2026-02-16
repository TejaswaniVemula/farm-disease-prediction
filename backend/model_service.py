import joblib
import numpy as np
from scipy.sparse import csr_matrix, hstack

class PredictorService:
    def __init__(self, model_path, tfidf_path, animal_enc_path, disease_enc_path):
        self.model = joblib.load(model_path)
        self.tfidf = joblib.load(tfidf_path)
        self.animal_enc = joblib.load(animal_enc_path)
        self.disease_enc = joblib.load(disease_enc_path)

    def predict_topk(self, animal: str, symptoms_text: str, k: int = 3):
        X_sym = self.tfidf.transform([symptoms_text])
        animal_encoded = self.animal_enc.transform([animal])[0]
        X_animal = csr_matrix([[animal_encoded]])
        X = hstack([X_sym, X_animal]).tocsr()

        proba = self.model.predict_proba(X)[0]
        top_idx = np.argsort(proba)[-k:][::-1]
        return [{"disease": self.disease_enc.classes_[i], "probability": float(proba[i])} for i in top_idx]
