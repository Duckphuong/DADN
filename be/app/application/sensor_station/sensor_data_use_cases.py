from typing import Optional

from app.application.common.exceptions import NotFoundError
from app.application.sensor_station.sensor_data_commands import (
    GetLatestSensorDataQuery,
    GetSensorClassificationQuery,
)
from app.application.sensor_station.sensor_data_interfaces import SensorDataRepository


# ---------------------------------------------------------------------------
# Ngưỡng phân loại nước
# ---------------------------------------------------------------------------

_HARDNESS_SOFT_MAX = 75.0       # mg/L
_HARDNESS_MODERATE_MAX = 150.0  # mg/L

_TURBIDITY_FRESH_MAX = 5.0      # NTU
_TURBIDITY_SLIGHTLY_MAX = 25.0  # NTU
_TURBIDITY_MODERATE_MAX = 75.0  # NTU

_ALKALINITY_LOW_MAX = 50.0      # mg/L
_ALKALINITY_HIGH_MIN = 150.0    # mg/L
_ALKALINITY_SAFE_RANGE = "80-120 mg/L"

_TEMP_COLD_MAX = 20.0           # °C
_TEMP_SAFE_MAX = 30.0           # °C


# ---------------------------------------------------------------------------
# GET /api/v1/sensors/latest
# ---------------------------------------------------------------------------

class GetLatestSensorDataUseCase:
    def __init__(self, sensor_data_repository: SensorDataRepository) -> None:
        self._repo = sensor_data_repository

    def execute(self, query: GetLatestSensorDataQuery) -> dict:
        doc = self._repo.get_latest(sensor_id=query.sensor_id)
        if doc is None:
            raise NotFoundError("No sensor data found")
        return doc


# ---------------------------------------------------------------------------
# GET /api/v1/sensors/classification
# ---------------------------------------------------------------------------

class GetSensorClassificationUseCase:
    def __init__(self, sensor_data_repository: SensorDataRepository) -> None:
        self._repo = sensor_data_repository

    def execute(self, query: GetSensorClassificationQuery) -> dict:
        doc = self._repo.get_latest(sensor_id=query.sensor_id)
        if doc is None:
            raise NotFoundError("No sensor data found")

        sd: dict = doc.get("sensor_data") or {}

        return {
            "sensor_id": str(doc.get("idSensor", "")),
            "created_at": doc.get("created_at"),
            "overall_quality": doc.get("quality_name"),
            "hardness": self._classify_hardness(sd.get("Hardness") or 0.0),
            "salinity": self._classify_salinity(sd.get("Turbidity") or 0.0),
            "alkalinity": self._classify_alkalinity(sd.get("Alkalinity") or 0.0),
            "temperature": self._classify_temperature(sd.get("Temp") or 0.0),
            "ph": round(sd.get("pH") or 0.0, 2),
            "do": round(sd.get("DO") or 0.0, 2),
        }

    # ------------------------------------------------------------------
    # Business rules — dễ chỉnh ngưỡng sau
    # ------------------------------------------------------------------

    @staticmethod
    def _classify_hardness(value: float) -> dict:
        if value <= _HARDNESS_SOFT_MAX:
            category = "Soft Water"
        elif value <= _HARDNESS_MODERATE_MAX:
            category = "Moderately Hard"
        else:
            category = "Hard Water"
        return {
            "category": category,
            "value_mgl": round(value, 2),
            "threshold_mgl": _HARDNESS_MODERATE_MAX,
        }

    @staticmethod
    def _classify_salinity(turbidity: float) -> dict:
        if turbidity <= _TURBIDITY_FRESH_MAX:
            level, note = "Fresh", "Độ đục thấp, phù hợp nuôi trồng thủy sản."
        elif turbidity <= _TURBIDITY_SLIGHTLY_MAX:
            level, note = "Slightly Saline", "Lượng nhỏ chất hòa tan, vẫn trong ngưỡng an toàn."
        elif turbidity <= _TURBIDITY_MODERATE_MAX:
            level, note = "Moderately Saline", "Độ đục trung bình, cần theo dõi thêm."
        else:
            level, note = "Highly Saline", "Độ đục cao, cần xử lý ngay."
        return {
            "level": level,
            "turbidity_ntu": round(turbidity, 2),
            "note": note,
        }

    @staticmethod
    def _classify_alkalinity(value: float) -> dict:
        if value < _ALKALINITY_LOW_MAX:
            level = "Low"
        elif value >= _ALKALINITY_HIGH_MIN:
            level = "High"
        else:
            level = "Moderate"
        return {
            "level": level,
            "value_mgl": round(value, 2),
            "safe_range": _ALKALINITY_SAFE_RANGE,
        }

    @staticmethod
    def _classify_temperature(value: float) -> dict:
        if value <= _TEMP_COLD_MAX:
            status = "Cold"
        elif value <= _TEMP_SAFE_MAX:
            status = "Safe"
        else:
            status = "Hot"
        return {
            "status": status,
            "value_celsius": round(value, 2),
        }