import os
import json
import joblib
import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


FEATURE_COLUMNS = [
    "Temp", "Turbidity", "DO", "BOD", "CO2",
    "pH", "Alkalinity", "Hardness", "Calcium",
    "Ammonia", "Nitrite", "Phosphorus", "H2S", "Plankton",
]


class AIModelService:
    def __init__(self):
        self.MODEL_DIR = "modelsAI"
        self.models = {}
        self.metadata = {}
        self.scaler = None

        os.makedirs(self.MODEL_DIR, exist_ok=True)

        self.load_models()

        if not self.models:
            print("No models found → training...")
            self.auto_train()
            self.load_models()

    # ================= AUTO TRAIN =================
    def auto_train(self):
        excel_file = "WQD.xlsx"

        if not os.path.exists(excel_file):
            print("No training file found")
            return {"error": "No training data"}

        df = pd.read_excel(excel_file)
        return self.train_model_from_dataframe(df)

    # ================= TRAIN =================
    def train_model_from_dataframe(self, df):
        df.columns = (
            df.columns
            .str.replace(r"\(.*?\)", "", regex=True)
            .str.replace("-", "")
            .str.strip()
        )

        if "Water Quality" not in df.columns:
            return {"error": "Missing 'Water Quality'"}

        for col in FEATURE_COLUMNS:
            if col not in df.columns:
                df[col] = 0

        df = df.fillna(0)

        X = df[FEATURE_COLUMNS]
        y = df["Water Quality"]

        # ===== SCALER =====
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        scaler_path = os.path.join(self.MODEL_DIR, "scaler.pkl")
        joblib.dump(scaler, scaler_path)

        models = {
            "RandomForest": RandomForestClassifier(),
            "GradientBoosting": GradientBoostingClassifier(),
            "LogisticRegression": LogisticRegression(max_iter=1000),
            "SVM": SVC(probability=True),
            "KNN": KNeighborsClassifier(),
        }

        metadata = {}

        for name, model in models.items():

            if name in ["LogisticRegression", "SVM", "KNN"]:
                model.fit(X_scaled, y)
                preds = model.predict(X_scaled)
                use_scaler = True
            else:
                model.fit(X, y)
                preds = model.predict(X)
                use_scaler = False

            acc = accuracy_score(y, preds)

            path = os.path.join(self.MODEL_DIR, f"{name}.pkl")
            joblib.dump(model, path)

            metadata[name] = {
                "accuracy": float(acc),
                "path": path,
                "use_scaler": use_scaler
            }

        with open(os.path.join(self.MODEL_DIR, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)

        self.metadata = metadata
        self.load_models()

        return {
            "message": "All models trained & saved",
            "accuracies": {k: v["accuracy"] for k, v in metadata.items()}
        }

    # ================= LOAD =================
    def load_models(self):
        self.models = {}

        metadata_path = os.path.join(self.MODEL_DIR, "metadata.json")
        scaler_path = os.path.join(self.MODEL_DIR, "scaler.pkl")

        if os.path.exists(scaler_path):
            self.scaler = joblib.load(scaler_path)

        if not os.path.exists(metadata_path):
            return

        with open(metadata_path, "r") as f:
            self.metadata = json.load(f)

        for name, info in self.metadata.items():
            if os.path.exists(info["path"]):
                try:
                    self.models[name] = joblib.load(info["path"])
                except Exception as e:
                    print(f"Failed to load {name}: {e}")

        print("Loaded models:", list(self.models.keys()))

    # ================= PREDICT =================
    def predict(self, data, model_name=None):
        if not self.models:
            return {"error": "No models loaded"}

        features = {col: float(data.get(col, 0)) for col in FEATURE_COLUMNS}
        df = pd.DataFrame([features])
        df_scaled = self.scaler.transform(df) if self.scaler else df

        if model_name:
            if model_name not in self.models:
                return {"error": "Model not found"}
            selected = {model_name: self.models[model_name]}
        else:
            selected = self.models

        results = []

        for name, model in selected.items():

            if self.metadata.get(name, {}).get("use_scaler"):
                input_data = df_scaled
            else:
                input_data = df

            prediction = model.predict(input_data)[0]

            if hasattr(model, "predict_proba"):
                proba = model.predict_proba(input_data)[0]
            else:
                proba = np.ones(len(model.classes_)) / len(model.classes_)

            proba = np.asarray(proba)
            class_values = model.classes_

            expected_class = float(np.dot(proba, class_values))
            wqi_score = (1 - expected_class / 2.0) * 100

            max_p = float(np.max(proba))
            confidence = max_p * 100.0

            label = self.getWqiLabel(wqi_score)
            risk_status, risk_level = self.getRiskFromWQILabel(label)

            delta = max(1.0, (1.0 - max_p) * 10.0)
            low = max(0.0, wqi_score - delta)
            high = min(100.0, wqi_score + delta)

            trend = "Stable" if delta <= 3.0 else "Unstable"

            results.append({
                "model": name,
                "accuracy": self.metadata.get(name, {}).get("accuracy", 0),
                "confidence": confidence,

                "wqi": {
                    "prediction": int(prediction),
                    "score": float(wqi_score),
                    "label": label
                },

                "risk": {
                    "status": risk_status,
                    "level": risk_level
                },

                "forecast_24h": {
                    "trend": trend,
                    "predicted_wqi_range": [float(low), float(high)],
                    "model_used": name,
                    "confidence_score": confidence
                }
            })

        results.sort(key=lambda x: (x["confidence"], x["accuracy"]), reverse=True)

        best = results[0]

        # ================= ENSEMBLE =================
        total = 0
        weight_sum = 0

        for m in results:
            w = m["accuracy"]
            total += m["wqi"]["score"] * w
            weight_sum += w

        ensemble_score = total / weight_sum if weight_sum > 0 else 0

        ensemble_label = self.getWqiLabel(ensemble_score)
        risk_status, risk_level = self.getRiskFromWQILabel(ensemble_label)

        ensemble_conf = np.mean([m["confidence"] for m in results])

        delta = max(1.0, (1.0 - ensemble_conf / 100.0) * 10.0)
        low = max(0.0, ensemble_score - delta)
        high = min(100.0, ensemble_score + delta)

        trend = "Stable" if delta <= 3.0 else "Unstable"

        return {
            "best_model": best["model"],
            "models": results,

            "ensemble": {
                "wqi": {
                    "score": float(ensemble_score),
                    "label": ensemble_label
                },
                "risk": {
                    "status": risk_status,
                    "level": risk_level
                },
                "confidence": float(ensemble_conf),
                "forecast_24h": {
                    "trend": trend,
                    "predicted_wqi_range": [float(low), float(high)]
                }
            },

            "summary": {
                "wqi": best["wqi"],
                "risk": best["risk"],
                "forecast_24h": best["forecast_24h"],
                "confidence": best["confidence"],
                "solution": self.solution_for(label),
            }
        }

    # ================= HELPER =================
    def getWqiLabel(self, score):
        if score >= 90:
            return "Excellent"
        if score >= 70:
            return "Good"
        return "Poor"

    def getRiskFromWQILabel(self, label):
        mapping = {
            "Excellent": ("Low Risk", 0),
            "Good": ("Medium Risk", 1),
            "Poor": ("High Risk", 2),
        }
        return mapping.get(label, ("Unknown", 7))
    
    
    def solution_for(self, quality_name: str) -> str:
        mapping = {
            "Excellent": "Monitor regularly.",
            "Good": "Consider treatment.",
            "Poor": "Immediate action required.",
        }
        return mapping.get(quality_name, "Check water quality parameters and adjust accordingly.")