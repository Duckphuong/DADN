from datetime import datetime, timezone, timedelta
from pymongo.errors import PyMongoError
from flask import current_app

from app.infrastructure.persistence.mongo.connection import get_mongo_database
from app.infrastructure.persistence.mongo.object_id import parse_object_id

# Ngưỡng thời gian: sensor không gửi data quá 15 phút → OFFLINE
OFFLINE_THRESHOLD_MINUTES = 60 * 24

SENSOR_FIELDS = [
    "Temp", "Turbidity", "DO", "BOD", "CO2", "pH",
    "Alkalinity", "Hardness", "Calcium", "Ammonia",
    "Nitrite", "Phosphorus", "H2S", "Plankton",
]

STATUS_ONLINE = "ONLINE"
STATUS_OFFLINE = "OFFLINE"
STATUS_ERROR = "ERROR"
ALERT_SERVICE = 'alert_service'

# ---------------------------------------------------------------------------
# Mapping firmware error message → tên sensor bị lỗi
# Sau này thêm sensor mới chỉ cần thêm vào đây, không cần sửa logic
# ---------------------------------------------------------------------------
FIRMWARE_ERROR_PATTERNS = {
    "DS18B20 sensor disconnected": "Temperature Sensor (DS18B20)",
    # "pH sensor disconnected":         "pH Sensor",
    # "DO sensor disconnected":         "DO Sensor",
    # "Turbidity sensor disconnected":  "Turbidity Sensor",
    # "Ammonia sensor disconnected":    "Ammonia Sensor",
}


class SensorHealthService:

    # ------------------------------------------------------------------
    # 1. Realtime detection — gọi từ /prediction/predict
    # ------------------------------------------------------------------

    def check_and_update(self, sensor_id: str, data: dict) -> str:
        """
        Kiểm tra data và cập nhật status + last_seen ngay lập tức.
        Trả về status để route quyết định có chạy AI hay không.

        Không raise exception — lỗi chỉ được log, không làm crash API predict.
        """
        status, error_message = self._detect_status(data)

        if status == STATUS_ERROR:
            # Log lỗi ra sensor_logs
            self._log_sensor_error(sensor_id, data, error_message)

            # Gửi alert
            alert_service = current_app.extensions.get(ALERT_SERVICE)
            if alert_service:
                alert_service.submit_sensor_error_alert(
                    current_app._get_current_object(),
                    str(sensor_id),
                    status,
                )

        self._update_sensor_status(sensor_id, status)
        return status

    def _detect_status(self, data: dict) -> tuple[str, str | None]:
        """
        Kiểm tra data hợp lệ hay không.
        Trả về (status, error_message).

        Các trường hợp ERROR:
          1. Firmware báo lỗi qua field "error" (DS18B20 disconnected, ...)
          2. Tất cả giá trị = 0
        """
        # Trường hợp 1: firmware gửi kèm field "error"
        firmware_error = data.get("error")
        if firmware_error:
            sensor_name = self._resolve_sensor_name(str(firmware_error))
            error_message = f"{sensor_name} disconnected: {firmware_error}"
            return STATUS_ERROR, error_message

        # Trường hợp 2: toàn bộ giá trị = 0
        values = [float(data.get(f) or 0) for f in SENSOR_FIELDS]
        if all(v == 0.0 for v in values):
            return STATUS_ERROR, "All sensor values are 0"

        return STATUS_ONLINE, None

    @staticmethod
    def _resolve_sensor_name(firmware_error: str) -> str:
        """
        Tra cứu tên sensor từ error message của firmware.
        Nếu không khớp pattern nào → trả về "Unknown Sensor".

        Để thêm sensor mới: chỉ cần thêm vào FIRMWARE_ERROR_PATTERNS ở trên.
        """
        for pattern, sensor_name in FIRMWARE_ERROR_PATTERNS.items():
            if pattern.lower() in firmware_error.lower():
                return sensor_name
        return "Unknown Sensor"

    def _log_sensor_error(self, sensor_id: str, data: dict, error_message: str) -> None:
        """
        Lưu log lỗi vào collection sensor_logs.

        Schema:
          sensor_id: str
          error_message: str       — mô tả lỗi (từ firmware hoặc hệ thống)
          sensor_data: dict        — snapshot data tại thời điểm lỗi
          created_at: datetime
        """
        db = get_mongo_database()
        if db is None:
            print("[SensorHealthService] MongoDB not connected, skip log")
            return

        try:
            db["sensor_logs"].insert_one({
                "sensor_id": str(sensor_id),
                "error_message": error_message,
                "sensor_data": {f: data.get(f) for f in SENSOR_FIELDS},
                "created_at": datetime.now(timezone.utc),
            })
            print(f"[SensorHealthService] Logged error for sensor {sensor_id}: {error_message}")
        except PyMongoError as e:
            print(f"[SensorHealthService] Failed to log sensor error: {e}")

    def _update_sensor_status(self, sensor_id: str, status: str) -> None:
        """Cập nhật status và last_seen vào sensor_informations."""
        db = get_mongo_database()
        if db is None:
            print("[SensorHealthService] MongoDB not connected, skip update")
            return

        try:
            oid = parse_object_id(sensor_id, field_name="sensor id")
        except Exception:
            print(f"[SensorHealthService] Invalid sensor_id: {sensor_id}")
            return

        try:
            result = db["sensor_informations"].update_one(
                {"_id": oid},
                {
                    "$set": {
                        "status": status,
                        "last_seen": datetime.now(timezone.utc),
                        "lastDateUpdate": datetime.now(timezone.utc),
                    }
                },
            )
            if result.matched_count == 0:
                print(f"[SensorHealthService] Sensor not found: {sensor_id}")
        except PyMongoError as e:
            print(f"[SensorHealthService] Failed to update sensor status: {e}")

    # ------------------------------------------------------------------
    # 2. Scheduler job — chạy mỗi 10 phút
    # ------------------------------------------------------------------

    def mark_offline_sensors(self) -> None:
        """
        1 query update_many duy nhất:
        Sensor có last_seen không tồn tại HOẶC last_seen < now - threshold
        → SET status = OFFLINE

        Không động vào sensor đang ERROR (đã có data, chỉ là data sai).
        """
        db = get_mongo_database()
        if db is None:
            print("[SensorHealthService] MongoDB not connected, skip scheduler job")
            return

        threshold = datetime.now(timezone.utc) - timedelta(minutes=OFFLINE_THRESHOLD_MINUTES)

        offline_query = {
            "isDeleted": False,
            "status": {"$ne": STATUS_ERROR},
            "$or": [
                {"last_seen": {"$exists": False}},
                {"last_seen": {"$lt": threshold}},
            ],
        }

        try:
            alert_service = current_app.extensions.get(ALERT_SERVICE)
            app = current_app._get_current_object()
            for sensor in db["sensor_informations"].find(offline_query, {"_id": 1}):
                sensor_id_str = str(sensor["_id"])
                if alert_service:
                    alert_service.submit_sensor_error_alert(
                        app,
                        sensor_id_str,
                        "OFFLINE",
                    )

            result = db["sensor_informations"].update_many(
                offline_query,
                {
                    "$set": {
                        "status": STATUS_OFFLINE,
                        "lastDateUpdate": datetime.now(timezone.utc),
                    }
                },
            )
            print(
                f"[SensorHealthService] Scheduler: marked {result.modified_count} sensor(s) as OFFLINE"
            )
        except PyMongoError as e:
            print(f"[SensorHealthService] Scheduler job failed: {e}")
