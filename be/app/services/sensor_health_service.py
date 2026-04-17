from datetime import datetime, timezone, timedelta
import threading
from pymongo.errors import PyMongoError
from flask import current_app
 
from app.infrastructure.persistence.mongo.connection import get_mongo_database
from app.infrastructure.persistence.mongo.object_id import parse_object_id
 
# Ngưỡng thời gian: sensor không gửi data quá 15 phút → OFFLINE
OFFLINE_THRESHOLD_MINUTES = 15
 
SENSOR_FIELDS = [
    "Temp", "Turbidity", "DO", "BOD", "CO2", "pH",
    "Alkalinity", "Hardness", "Calcium", "Ammonia",
    "Nitrite", "Phosphorus", "H2S", "Plankton",
]
 
STATUS_ONLINE = "ONLINE"
STATUS_OFFLINE = "OFFLINE"
STATUS_ERROR = "ERROR"
ALERT_SERVICE = 'alert_service'
 
 
class SensorHealthService:
 
    # 1. Realtime detection — gọi từ /prediction/predict
 
    def check_and_update(self, sensor_id: str, data: dict) -> None:
        """
        Kiểm tra data và cập nhật status + last_seen ngay lập tức.
        Gọi sau khi nhận data từ sensor, trước khi trả response.
 
        Không raise exception — lỗi chỉ được log, không làm crash API predict.
        """
        status = self._detect_status(data)
        if status == STATUS_ERROR:
            alert_service = current_app.extensions.get(ALERT_SERVICE)
            if alert_service:
                threading.Thread(
                    target=alert_service.send_sensor_error_alert, 
                    args=(str(sensor_id), status)
                ).start()
        self._update_sensor_status(sensor_id, status)
        return status
 
    def _detect_status(self, data: dict) -> str:
        """
        Kiểm tra data có toàn 0 không.
        Trả về ERROR nếu tất cả field đều = 0, ngược lại ONLINE.
        """
        values = [float(data.get(f) or 0) for f in SENSOR_FIELDS]
        if all(v == 0.0 for v in values):
            return STATUS_ERROR
        return STATUS_ONLINE
 
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
            db["sensor_informations"].update_one(
                {"_id": oid},
                {
                    "$set": {
                        "status": status,
                        "last_seen": datetime.now(timezone.utc),
                        "lastDateUpdate": datetime.now(timezone.utc),
                    }
                },
            )
        except PyMongoError as e:
            print(f"[SensorHealthService] Failed to update sensor status: {e}")
 
    # 2. Scheduler job — chạy mỗi 10 phút
 
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
            for sensor in db["sensor_informations"].find(offline_query, {"_id": 1}):
                sensor_id_str = str(sensor["_id"])
                if alert_service:
                    threading.Thread(
                        target=alert_service.send_sensor_error_alert, 
                        args=(sensor_id_str, "OFFLINE")
                    ).start()

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
 