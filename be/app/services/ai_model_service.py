import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

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
        prediction = self.model.predict(df)[0]

        # Map numeric prediction to quality name
        quality_mapping = {
            0: "Poor",
            1: "Moderate", 
            2: "Good"
        }
        quality_name = quality_mapping.get(prediction, "Unknown")

        return {
            "quality_label": int(prediction),
            "quality_name": quality_name,
            "solution": self._solution_for(quality_name),
        }

    def _solution_for(self, quality_name: str) -> str:
        mapping = {
            "Good": "Monitor regularly.",
            "Moderate": "Consider treatment.",
            "Poor": "Immediate action required.",
        }
        return mapping.get(quality_name, "Check water quality parameters and adjust accordingly.")