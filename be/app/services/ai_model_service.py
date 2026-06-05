import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR

from app.infrastructure.external.weather_service import get_weather_data
from app.services.solution_ai_service import SolutionAIService


MODEL_VERSION = 2
TRAINING_DATA_FILES = ("dataset_DADN_Cleaned.xlsx",)
TARGET_CANDIDATES = ("WQI",)
FEATURE_COLUMNS = [
	"Nhiệt độ",
	"pH",
	"DO",
	"Độ dẫn",
	"Độ kiềm",
	"N-NO2",
	"N-NH4",
	"P-PO4",
	"H2S",
	"TSS",
	"COD",
	"Aeromonas tổng số",
	"Coliform",
]
FEATURE_ALIASES = {
	"Nhiệt độ": ["Nhiệt độ", "Temp", "Temperature", "TemperatureC", "Temperature_C"],
	"pH": ["pH", "ph"],
	"DO": ["DO", "Dissolved Oxygen", "Dissolved_Oxygen"],
	"Độ dẫn": ["Độ dẫn", "Conductivity", "EC", "Conductivity_uS"],
	"Độ kiềm": ["Độ kiềm", "Alkalinity"],
	"N-NO2": ["N-NO2", "NO2", "Nitrite"],
	"N-NH4": ["N-NH4", "NH4", "Ammonia"],
	"P-PO4": ["P-PO4", "PO4", "Phosphorus"],
	"H2S": ["H2S"],
	"TSS": ["TSS", "Turbidity"],
	"COD": ["COD", "BOD", "Chemical Oxygen Demand", "Biochemical Oxygen Demand"],
	"Aeromonas tổng số": ["Aeromonas tổng số", "Aeromonas", "Aeromonas_count"],
	"Coliform": ["Coliform", "Coliform_count"],
}

solution_service = SolutionAIService()


class AIModelService:
	def __init__(self):
		self.MODEL_DIR = "modelsAI"
		self.models = {}
		self.metadata = {}
		self.scaler = None
		self.target_column = "WQI"
		self.training_source = None

		os.makedirs(self.MODEL_DIR, exist_ok=True)

		self.load_models()

		if not self.models:
			print("No regression models found - training from dataset...")
			self.auto_train()
			self.load_models()

	def test_db(self):
		return {
			"status": "ok",
			"task": "regression",
			"loaded_models": list(self.models.keys()),
			"target_column": self.target_column,
			"training_source": self.training_source,
		}

	# ================= FIELD NORMALIZATION =================
	def _normalize_field_name(self, field_name: str) -> str:
		"""
		Convert any field name alias to canonical Vietnamese name.
		E.g.: "Temp" -> "Nhiệt độ", "Turbidity" -> "TSS", "BOD" -> "COD"
		Returns the canonical name, or the input if not found.
		"""
		for canonical_name, aliases in FEATURE_ALIASES.items():
			if field_name in aliases:
				return canonical_name
		return field_name

	def normalize_sensor_data(self, data: dict) -> dict:
		"""
		Normalize all field names in sensor data dict to canonical Vietnamese names.
		Only includes fields that are in FEATURE_COLUMNS (canonical names).
		"""
		normalized = {}
		for key, value in data.items():
			canonical_name = self._normalize_field_name(key)
			# Only include if it's a known field
			if canonical_name in FEATURE_COLUMNS:
				normalized[canonical_name] = value
		# Preserve non-sensor fields like sensorId, idSensor, error, etc.
		for key in ["sensorId", "idSensor", "error"]:
			if key in data:
				normalized[key] = data[key]
		return normalized

	# ================= AUTO TRAIN =================
	def auto_train(self):
		training_file = self._resolve_training_file()

		if training_file is None:
			print("No training file found")
			return {"error": "No training data"}

		df = pd.read_excel(training_file)
		return self.train_model_from_dataframe(df, source_name=os.path.basename(training_file))

	def train_model_from_db(self):
		return self.auto_train()

	def train_model_from_file(self, file):
		try:
			df = pd.read_excel(file)
		except Exception as exc:
			return {"error": f"Failed to read uploaded file: {exc}"}
		return self.train_model_from_dataframe(df, source_name=getattr(file, "filename", "uploaded_file"))

	# ================= TRAIN =================
	def train_model_from_dataframe(self, df, source_name=None):
		normalized_df = self._prepare_training_dataframe(df)
		target_column = self._detect_target_column(normalized_df)

		if target_column is None:
			return {"error": "Missing WQI target column"}

		available_features = [col for col in FEATURE_COLUMNS if col in normalized_df.columns]
		if not available_features:
			return {"error": "Missing training features"}

		working_df = normalized_df[available_features + [target_column]].copy()
		working_df = working_df.dropna(subset=[target_column])
		working_df[available_features] = working_df[available_features].apply(
			pd.to_numeric, errors="coerce"
		)
		working_df[available_features] = working_df[available_features].fillna(
			working_df[available_features].median(numeric_only=True)
		)
		working_df = working_df.dropna(subset=available_features, how="all")
		working_df = working_df.replace([np.inf, -np.inf], np.nan).dropna(subset=[target_column])

		if working_df.empty:
			return {"error": "No usable rows in dataset"}

		x = working_df[available_features]
		y = pd.to_numeric(working_df[target_column], errors="coerce")
		valid_rows = y.notna()
		x = x.loc[valid_rows].copy()
		y = y.loc[valid_rows].copy()

		if len(x) < 10:
			return {"error": "Not enough valid training rows"}

		X_train, X_test, y_train, y_test = train_test_split(
			x,
			y,
			test_size=0.2,
			random_state=42,
		)

		scaler = StandardScaler()
		X_train_scaled = scaler.fit_transform(X_train)
		X_test_scaled = scaler.transform(X_test)

		scaler_path = os.path.join(self.MODEL_DIR, "scaler.pkl")
		joblib.dump(scaler, scaler_path)

		models = {
			"RandomForestRegressor": RandomForestRegressor(n_estimators=300, random_state=42),
			"GradientBoostingRegressor": GradientBoostingRegressor(random_state=42),
			"LinearRegression": LinearRegression(),
			"SVR": SVR(C=10.0, kernel="rbf"),
			"KNNRegressor": KNeighborsRegressor(n_neighbors=5),
		}

		scaled_models = {"LinearRegression", "SVR", "KNNRegressor"}
		metadata = {
			"_meta": {
				"version": MODEL_VERSION,
				"task": "regression",
				"target_column": target_column,
				"feature_columns": available_features,
				"source_name": source_name or "dataset.xlsx",
			}
		}

		for name, model in models.items():
			if name in scaled_models:
				model.fit(X_train_scaled, y_train)
				preds = model.predict(X_test_scaled)
				use_scaler = True
			else:
				model.fit(X_train, y_train)
				preds = model.predict(X_test)
				use_scaler = False

			mae = float(mean_absolute_error(y_test, preds))
			rmse = float(root_mean_squared_error(y_test, preds))
			r2 = float(r2_score(y_test, preds))
			score = max(0.0, min(1.0, r2 if np.isfinite(r2) else 0.0))

			path = os.path.join(self.MODEL_DIR, f"{name}.pkl")
			joblib.dump(model, path)

			metadata[name] = {
				"score": score,
				"accuracy": score,
				"r2": r2,
				"mae": mae,
				"rmse": rmse,
				"path": path,
				"use_scaler": use_scaler,
				"task": "regression",
			}

		with open(os.path.join(self.MODEL_DIR, "metadata.json"), "w", encoding="utf-8") as f:
			json.dump(metadata, f, indent=2, ensure_ascii=False)

		self.metadata = metadata
		self.training_source = metadata["_meta"]["source_name"]
		self._build_reference_profile(x, target_column=target_column)
		self.load_models()

		return {
			"message": "Regression models trained & saved",
			"target_column": target_column,
			"features": available_features,
			"metrics": {
				k: {
					"score": v["score"],
					"r2": v["r2"],
					"mae": v["mae"],
					"rmse": v["rmse"],
				} for k, v in metadata.items() if k != "_meta"
			},
		}

	# ================= LOAD =================
	def load_models(self):
		self.models = {}
		self.scaler = None

		metadata_path = os.path.join(self.MODEL_DIR, "metadata.json")
		scaler_path = os.path.join(self.MODEL_DIR, "scaler.pkl")

		if os.path.exists(scaler_path):
			try:
				self.scaler = joblib.load(scaler_path)
			except Exception as exc:
				print(f"Failed to load scaler: {exc}")

		if not os.path.exists(metadata_path):
			return

		with open(metadata_path, "r", encoding="utf-8") as f:
			self.metadata = json.load(f)

		meta = self.metadata.get("_meta", {})
		if meta.get("task") != "regression" or meta.get("version") != MODEL_VERSION:
			print("Incompatible model metadata detected - retraining required")
			self.models = {}
			self.metadata = {}
			self.scaler = None
			return

		self.target_column = meta.get("target_column", self.target_column)
		self.training_source = meta.get("source_name", self.training_source)

		for name, info in self.metadata.items():
			if name == "_meta":
				continue
			if os.path.exists(info.get("path", "")):
				try:
					self.models[name] = joblib.load(info["path"])
				except Exception as exc:
					print(f"Failed to load {name}: {exc}")

		print("Loaded regression models:", list(self.models.keys()))

	# ================= PREDICT =================
	def predict(self, data, model_name=None):
		if not self.models:
			return {"error": "No models loaded"}

		features = self._build_feature_frame(data)
		features_scaled = self.scaler.transform(features) if self.scaler else features

		if model_name:
			if model_name not in self.models:
				return {"error": "Model not found"}
			selected = {model_name: self.models[model_name]}
		else:
			selected = self.models

		results = []

		for name, model in selected.items():
			model_info = self.metadata.get(name, {})
			input_data = features_scaled if model_info.get("use_scaler") else features
			prediction_value = float(model.predict(input_data)[0])
			prediction_value = float(np.clip(prediction_value, 0.0, 100.0))

			mae = float(model_info.get("mae", 0.0))
			rmse = float(model_info.get("rmse", 0.0))
			r2 = float(model_info.get("r2", 0.0))
			confidence = max(0.0, min(100.0, model_info.get("score", 0.0) * 100.0))

			label = self.getWqiLabel(prediction_value)
			# abnormal_parameters
			abnormal_parameters = []
			if label in ["Good", "Poor"]:
				abnormal_parameters = self.analyze_abnormal_parameters(data)

			risk_status, risk_level = self.getRiskFromWQILabel(label)

			delta = max(1.0, rmse * 1.5 if rmse > 0 else 3.0)
			low = max(0.0, prediction_value - delta)
			high = min(100.0, prediction_value + delta)
			trend = "Stable" if delta <= 3.0 else "Unstable"

			results.append({
				"model": name,
				"accuracy": model_info.get("score", 0.0),
				"confidence": confidence,
				"metrics": {
					"r2": r2,
					"mae": mae,
					"rmse": rmse,
				},
				"wqi": {
					"prediction": prediction_value,
					"score": prediction_value,
					"label": label,
				},
				"risk": {
					"status": risk_status,
					"level": risk_level,
				},
				"forecast_24h": {
					"trend": trend,
					"predicted_wqi_range": [float(low), float(high)],
					"model_used": name,
					"confidence_score": confidence,
				},
			})

		results.sort(key=lambda x: (x["accuracy"], x["confidence"]), reverse=True)
		best = results[0]

		weights = np.array([max(item["accuracy"], 1e-6) for item in results], dtype=float)
		weights = weights / weights.sum()
		model_predictions = np.array([item["wqi"]["score"] for item in results], dtype=float)
		ensemble_score = float(np.dot(model_predictions, weights))
		ensemble_score = float(np.clip(ensemble_score, 0.0, 100.0))
		ensemble_label = self.getWqiLabel(ensemble_score)
		risk_status, risk_level = self.getRiskFromWQILabel(ensemble_label)
		ensemble_conf = float(np.mean([item["confidence"] for item in results]))
		ensemble_rmse = float(np.dot(np.array([item["metrics"]["rmse"] for item in results]), weights))
		delta = max(1.0, ensemble_rmse * 1.5 if ensemble_rmse > 0 else 3.0)
		low = max(0.0, ensemble_score - delta)
		high = min(100.0, ensemble_score + delta)
		trend = "Stable" if delta <= 3.0 else "Unstable"

		try:
			weather_info = get_weather_data(10.8231, 106.6297)
			temp_result = {
				"summary": {
					"wqi": best["wqi"],
					"forecast_24h": best["forecast_24h"],
					"abnormal_parameters": abnormal_parameters,
				},
			}
			final_solution = solution_service.generate_advanced_solution(
				sensor_data=data,
				ai_prediction_result=temp_result,
				weather_data=weather_info,
			)
		except Exception as exc:
			print(f"Lỗi khi gọi Groq/Weather trong ai_model_service: {exc}")
			final_solution = self.solution_for(best["wqi"]["label"])
			weather_info = None

		return {
			"best_model": best["model"],
			"models": results,
			"ensemble": {
				"wqi": {
					"score": float(ensemble_score),
					"label": ensemble_label,
				},
				"risk": {
					"status": risk_status,
					"level": risk_level,
				},
				"confidence": float(ensemble_conf),
				"forecast_24h": {
					"trend": trend,
					"predicted_wqi_range": [float(low), float(high)],
				},
			},
			"summary": {
				"wqi": best["wqi"],
				"risk": best["risk"],
				"accuracy": best["accuracy"],
				"metrics": best["metrics"],
				"forecast_24h": best["forecast_24h"],
				"confidence": best["confidence"],
				"solution": final_solution,
				"weather": weather_info,
				"abnormal_parameters": abnormal_parameters,
			},
		}

	# ================= HELPERS =================
	def _resolve_training_file(self):
		for file_name in TRAINING_DATA_FILES:
			if os.path.exists(file_name):
				return file_name
		return None

	def _prepare_training_dataframe(self, df):
		normalized_df = df.copy()
		normalized_df.columns = [str(col).strip() for col in normalized_df.columns]
		normalized_df = normalized_df.replace({",": "."}, regex=True)
		return normalized_df

	def _detect_target_column(self, df):
		for candidate in TARGET_CANDIDATES:
			if candidate in df.columns:
				self.target_column = candidate
				return candidate
		return None

	def _build_feature_frame(self, data):
		features = {}
		for column in FEATURE_COLUMNS:
			value = None
			for alias in FEATURE_ALIASES.get(column, [column]):
				if alias in data and data.get(alias) not in (None, ""):
					value = data.get(alias)
					break
			features[column] = self._to_float(value)
		return pd.DataFrame([features])

	def _build_reference_profile(self, feature_df, *, target_column):
		if feature_df.empty:
			return

		profile = {}
		for column in FEATURE_COLUMNS:
			if column not in feature_df.columns:
				continue
			series = pd.to_numeric(feature_df[column], errors="coerce").dropna()
			if series.empty:
				continue
			stats = {
				"mean": round(float(series.mean()), 2),
				"min_safe": round(float(series.quantile(0.05)), 2),
				"max_safe": round(float(series.quantile(0.95)), 2),
			}
			for alias in FEATURE_ALIASES.get(column, [column]):
				profile[alias] = stats

		profile["__meta__"] = {
			"target_column": target_column,
			"source": self.training_source or "dataset.xlsx",
		}

		profile_path = os.path.join(self.MODEL_DIR, "good_water_profile.json")
		with open(profile_path, "w", encoding="utf-8") as f:
			json.dump(profile, f, indent=4, ensure_ascii=False)

	def _to_float(self, value, default=0.0):
		if value is None:
			return default
		if isinstance(value, (int, float, np.number)):
			if np.isnan(value):
				return default
			return float(value)
		text_value = str(value).strip()
		if not text_value:
			return default
		text_value = text_value.replace(",", ".")
		try:
			return float(text_value)
		except ValueError:
			return default

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
	
	def analyze_abnormal_parameters(self, sensor_data: dict):
		profile_path = os.path.join(self.MODEL_DIR, "good_water_profile.json")

		if not os.path.exists(profile_path):
			return []

		with open(profile_path, "r", encoding="utf-8") as f:
			profile = json.load(f)

		results = []

		# nhóm chỉ số xử lý theo kiểu riêng
		temperature_fields = {"Nhiệt độ"}
		bacteria_fields = {"Aeromonas tổng số", "Coliform"}
		oxygen_fields = {"DO"}

		for field in FEATURE_COLUMNS:
			if field not in sensor_data:
				continue

			if field not in profile:
				continue

			value = self._to_float(sensor_data.get(field))

			ref = profile[field]

			min_safe = ref.get("min_safe")
			max_safe = ref.get("max_safe")

			if min_safe is None or max_safe is None:
				continue

			# ================= BELOW SAFE =================
			if value < min_safe:
				diff = round(min_safe - value, 2)

				# nhiệt độ
				if field in temperature_fields:
					message = f"{field} thấp hơn mức an toàn {diff}°C"

				# DO
				elif field in oxygen_fields:
					message = f"{field} thấp hơn mức cần thiết {diff} mg/L"

				# mặc định
				else:
					times = round(min_safe / max(value, 0.0001), 2)
					message = (
						f"{field} thấp hơn ngưỡng an toàn "
						f"{times} lần"
					)

				results.append({
					"parameter": field,
					"status": "below_safe",
					"value": value,
					"safe_min": min_safe,
					"difference": diff,
					"message": message,
				})

			# ================= ABOVE SAFE =================
			elif value > max_safe:
				diff = round(value - max_safe, 2)
				times = round(value / max_safe, 2)

				# vi sinh
				if field in bacteria_fields:
					message = (
						f"Mật độ {field} vượt ngưỡng an toàn "
						f"gấp {times} lần"
					)

				# nhiệt độ
				elif field in temperature_fields:
					message = (
						f"{field} cao hơn mức an toàn "
						f"{diff}°C"
					)

				# pH
				elif field == "pH":
					message = (
						f"pH vượt khỏi khoảng an toàn "
						f"{diff} đơn vị"
					)

				# mặc định
				else:
					message = (
						f"{field} vượt ngưỡng an toàn "
						f"gấp {times} lần"
					)

				results.append({
					"parameter": field,
					"status": "above_safe",
					"value": value,
					"safe_max": max_safe,
					"times_exceeded": times,
					"difference": diff,
					"message": message,
				})

		return results