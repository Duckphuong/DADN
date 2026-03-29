import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
import numpy as np

from app.database.db import db
from app.models.input_model import InputModel, OutputModel


FEATURE_COLUMNS = [
    "Temp",
    "Turbidity",
    "DO",
    "BOD",
    "CO2",
    "pH",
    "Alkalinity",
    "Hardness",
    "Calcium",
    "Ammonia",
    "Nitrite",
    "Phosphorus",
    "H2S",
    "Plankton",
]


class AIModelService:
    def __init__(self):
        self.MODEL_PATH = "water_model.pkl"
        self.model = None
        self.load_model()
    
    def auto_train(self):
        # Remove old model file to force retrain
        if os.path.exists(self.MODEL_PATH):
            os.remove(self.MODEL_PATH)
            print("🗑️  Removed old model file")
        
        # Try to train from WQD.xlsx file first
        excel_file = "WQD.xlsx"
        if os.path.exists(excel_file):
            print("📊 Training from WQD.xlsx file...")
            try:
                df = pd.read_excel(excel_file)
                result = self.train_model_from_dataframe(df)
                if "error" not in result:
                    print("✅ Auto-trained AI model from WQD.xlsx")
                    return
                else:
                    print(f"❌ Failed to train from WQD.xlsx: {result['error']}")
            except Exception as e:
                print(f"❌ Error reading WQD.xlsx: {e}")
        
        # Fallback to training from database
        print("📊 Training from database...")
        result = self.train_model_from_db()
        if "error" not in result:
            print("✅ Auto-trained AI model from database")
        else:
            print("⚠️  No labeled data available for training - model not loaded")

    def load_model(self):
        if os.path.exists(self.MODEL_PATH):
            self.model = joblib.load(self.MODEL_PATH)

    def test_db(self):
        count = OutputModel.query.count()
        return {"record_count": count}

    def train_model_from_file(self, file):
        df = pd.read_excel(file)
        return self.train_model_from_dataframe(df)

    def train_model_from_dataframe(self, df):
        # Normalize column names
        df.columns = (
            df.columns
            .str.replace(r"\(.*?\)", "", regex=True)
            .str.replace("-", "")
            .str.strip()
        )

        if "Water Quality" not in df.columns:
            return {"error": "File must contain a 'Water Quality' column"}

        # Prepare data for training
        X = df[FEATURE_COLUMNS]
        y = df["Water Quality"]

        if len(X) < 2:
            return {"error": "Need at least 2 samples for training"}

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.model = RandomForestClassifier()
        self.model.fit(X_train, y_train)

        acc = accuracy_score(y_test, self.model.predict(X_test))
        joblib.dump(self.model, self.MODEL_PATH)

        return {
            "message": "Model trained successfully from Excel file",
            "accuracy": float(acc),
        }

    def train_model_from_db(self):
        records = OutputModel.query.filter(OutputModel.quality_name.isnot(None)).all()

        if not records:
            return {"error": "No labeled data available for training"}

        df = pd.DataFrame([{
            **{col: getattr(r, col) for col in FEATURE_COLUMNS},
            "label": r.quality_name,
        } for r in records])

        X = df[FEATURE_COLUMNS]
        y = df["label"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.model = RandomForestClassifier()
        self.model.fit(X_train, y_train)

        acc = accuracy_score(y_test, self.model.predict(X_test))
        joblib.dump(self.model, self.MODEL_PATH)

        return {
            "message": "Model trained successfully from DB",
            "accuracy": float(acc),
        }

    def predict(self, data):
        if self.model is None:
            self.load_model()
            if self.model is None:
                return {"error": "Model not loaded"}

        features = {col: float(data.get(col, 0)) for col in FEATURE_COLUMNS}
        df = pd.DataFrame([features])

        # Probabilities for classes [0,1,2]
        proba = self.model.predict_proba(df)[0]
        proba = np.asarray(proba, dtype=float)

        # continuous expected class in [0,2]
        expected_class = float(np.dot(proba, np.array([0.0, 1.0, 2.0])))

        # scale to WQI [0,100] - chưa làm tròn
        wqi_score = expected_class / 2.0 * 100.0

        # confidence %
        max_p = float(np.max(proba))
        confidence_score = max_p * 100.0

        wqi_label = self.getWqiLabel(wqi_score)
        risk_status, risk_level = self.getRiskFromWQILabel(wqi_label)

        # forecast_24h range
        delta = max(1.0, (1.0 - max_p) * 10.0)
        low = max(0.0, wqi_score - delta)
        high = min(100.0, wqi_score + delta)

        trend = "Stable" if delta <= 3.0 else "Unstable"

        return {
            "wqi": {"score": float(wqi_score), "max": 100, "label": wqi_label},
            "contamination_risk": {"status": risk_status, "risk_level": int(risk_level)},
            "forecast_24h": {
                "trend": trend,
                "predicted_wqi_range": [float(low), float(high)],
                "model_used": "Random Forest",
                "confidence_score": float(confidence_score),
            },
        }
        
    def getWqiLabel(self, wqi_score: float) -> str:
        if wqi_score >= 90:
            return "Excellent"
        if wqi_score >= 70:
            return "Good"
        if wqi_score >= 50:
            return "Fair"
        return "Poor"

    def getRiskFromWQILabel(self, label: str):
        mapping = {
            "Excellent": ("Low Risk", 1),
            "Good": ("Medium Risk", 2),
            "Fair": ("High Risk", 3),
            "Poor": ("High Risk", 3),
        }
        return mapping.get(label, ("Unknown", 0))

    def _solution_for(self, quality_name: str) -> str:
        mapping = {
            "Good": "Monitor regularly.",
            "Moderate": "Consider treatment.",
            "Poor": "Immediate action required.",
        }
        return mapping.get(quality_name, "Check water quality parameters and adjust accordingly.")