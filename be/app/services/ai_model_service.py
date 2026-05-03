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

from app.infrastructure.external.weather_service import get_weather_data
from app.services.solution_ai_service import SolutionAIService


FEATURE_COLUMNS = [
	"Temp", "Turbidity", "DO", "BOD", "CO2",
	"pH", "Alkalinity", "Hardness", "Calcium",
	"Ammonia", "Nitrite", "Phosphorus", "H2S", "Plankton",
]
solution_service = SolutionAIService()

class AIModelService:
	def __init__(self):
		self.MODEL_DIR = "modelsAI"
		self.models = {}
		self.metadata = {}
		self.scaler = None

		os.makedirs(self.MODEL_DIR, exist_ok=True)

		self.load_models()

		if not self.models:
			print("No models found - training...")
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

		# ===== SPLIT DATA =====
		X_train, X_test, y_train, y_test = train_test_split(
			X, y, test_size=0.2, random_state=42, stratify=y
		)

		# ===== SCALER =====
		scaler = StandardScaler()
		X_train_scaled = scaler.fit_transform(X_train)
		X_test_scaled = scaler.transform(X_test)

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
				model.fit(X_train_scaled, y_train)
				preds = model.predict(X_test_scaled)
				use_scaler = True
			else:
				model.fit(X_train, y_train)
				preds = model.predict(X_test)
				use_scaler = False

			acc = accuracy_score(y_test, preds)

			path = os.path.join(self.MODEL_DIR, f"{name}.pkl")
			joblib.dump(model, path)

			metadata[name] = {
				"accuracy": float(acc),
				"path": path,
				"use_scaler": use_scaler
			}

		with open(os.path.join(self.MODEL_DIR, "metadata.json"), "w") as f:
			json.dump(metadata, f, indent=2)

		# =====================================================================
		# [BỔ SUNG: TẠO HỒ SƠ NƯỚC CHUẨN TỪ MODEL TỐT NHẤT]
		# =====================================================================
		try:
			# 1. Tìm model có accuracy cao nhất trong dict metadata
			best_model_name = max(metadata, key=lambda k: metadata[k]["accuracy"])
			best_model = models[best_model_name]
			
			# 2. Xác định index của nhãn Tốt (Hỗ trợ nhãn là 0, 1 hoặc Excellent, Good)
			classes = list(best_model.classes_)
			good_indices = [i for i, c in enumerate(classes) if str(c) in ["0", "1", "Excellent", "Good"]]

			if good_indices:
				# 3. Lấy xác suất dự đoán (Dùng X_scaled hoặc X tùy vào cấu hình model)
				if metadata[best_model_name]["use_scaler"]:
					X_full_scaled = scaler.transform(X)
					probs = best_model.predict_proba(X_full_scaled)
				else:
					probs = best_model.predict_proba(X)
				
				# 4. Tính tổng xác suất và lọc các mẫu model tốt (>= 85%)
				good_probs = np.sum(probs[:, good_indices], axis=1)
				certified_indices = np.where(good_probs >= 0.85)[0]
				certified_df = X.iloc[certified_indices]
				
				# 5. Tính Tứ phân vị (5% - 95%) để tạo vùng an toàn chuẩn
				if not certified_df.empty:
					good_profile = {}
					for col in FEATURE_COLUMNS:
						good_profile[col] = {
							"mean": round(float(certified_df[col].mean()), 2),
							"min_safe": round(float(certified_df[col].quantile(0.05)), 2),
							"max_safe": round(float(certified_df[col].quantile(0.95)), 2)
						}
					
					profile_path = os.path.join(self.MODEL_DIR, "good_water_profile.json")
					with open(profile_path, "w", encoding="utf-8") as f:
						json.dump(good_profile, f, indent=4)
					print(f"Đã tạo good_water_profile.json từ model {best_model_name} với {len(certified_df)} mẫu.")
		except Exception as e:
			print(f"Lỗi khi tạo good_water_profile: {e}")

		# =====================================================================
		# [BỔ SUNG: TẠO HỒ SƠ NƯỚC CHUẨN TỪ MODEL TỐT NHẤT]
		# =====================================================================	

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

		# ===========================================================
        # [TÍCH HỢP SOLUTION (GROQ) & WEATHER]
        # ===========================================================
		try:
			weather_info = get_weather_data(10.8231, 106.6297)
			temp_result = {
				"summary": {
					"wqi": best["wqi"],
					"forecast_24h": best["forecast_24h"]
				}
			}
			
			final_solution = solution_service.generate_advanced_solution(
				sensor_data=data,
				ai_prediction_result=temp_result,
				weather_data=weather_info
			)
		except Exception as e:
			print(f"Lỗi khi gọi Groq/Weather trong ai_model_service: {e}")
			final_solution = self.solution_for(best["wqi"]["label"])
			weather_info = None

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
				"accuracy": best["accuracy"],
				"forecast_24h": best["forecast_24h"],
				"confidence": best["confidence"],
				"solution": final_solution,
				"weather": weather_info
			}
		}

	# ================= HELPER =================
	def getWqiLabel(self, score):
		if score >= 80:
			return "Excellent"
		if score >= 40:
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