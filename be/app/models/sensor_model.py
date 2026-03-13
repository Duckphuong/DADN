from datetime import datetime

from app.database.db import db


class SensorData(db.Model):
    __tablename__ = "sensor_data"

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(100), nullable=False, index=True)
    value = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "value": self._serialized_value(),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }

    def _serialized_value(self):
        return int(self.value) if float(self.value).is_integer() else self.value
