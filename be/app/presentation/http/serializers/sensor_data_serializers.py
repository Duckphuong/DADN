def serialize_latest_sensor(doc: dict) -> dict:
    """
    Response cho GET /api/v1/sensors/latest.
    Field names khớp với SensorCard (title, value, unit) và types/water.ts (SensorData).
    """
    sd: dict = doc.get("sensor_data") or {}

    return {
        "id": doc.get("_id"),
        "sensor_id": doc.get("idSensor"),
        "created_at": doc.get("created_at"),
        "quality_label": doc.get("quality_label"),
        "quality_name": doc.get("quality_name"),
        "solution": doc.get("solution"),
        "sensor_data": {
            "pH":         sd.get("pH"),
            "Temp":       sd.get("Temp"),
            "DO":         sd.get("DO"),
            "Turbidity":  sd.get("Turbidity"),
            "Hardness":   sd.get("Hardness"),
            "Alkalinity": sd.get("Alkalinity"),
            "Ammonia":    sd.get("Ammonia"),
            "BOD":        sd.get("BOD"),
            "CO2":        sd.get("CO2"),
            "Calcium":    sd.get("Calcium"),
            "H2S":        sd.get("H2S"),
            "Nitrite":    sd.get("Nitrite"),
            "Phosphorus": sd.get("Phosphorus"),
            "Plankton":   sd.get("Plankton"),
        },
    }


def serialize_classification(result: dict) -> dict:
    """
    Response cho GET /api/v1/sensors/classification.
    Field names khớp với WaterClassificationPanel:
      - hardness.category  → "Hard Water" / "Soft Water" / "Moderately Hard"
      - hardness.value_mgl → hiển thị số mg/L
      - alkalinity.level   → "Low" / "Moderate" / "High"
      - temperature.status → "Cold" / "Safe" / "Hot"
      - ph, do             → circular gauge
    """
    return {
        "sensor_id":       result.get("sensor_id"),
        "created_at":      result.get("created_at"),
        "overall_quality": result.get("overall_quality"),
        "hardness":        result.get("hardness"),
        "salinity":        result.get("salinity"),
        "alkalinity":      result.get("alkalinity"),
        "temperature":     result.get("temperature"),
        "ph":              result.get("ph"),
        "do":              result.get("do"),
    }