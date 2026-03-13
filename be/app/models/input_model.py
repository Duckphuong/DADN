from datetime import datetime

from app.database.db import db


class InputModel(db.Model):
    __tablename__ = "input_model"

    id = db.Column(db.Integer, primary_key=True)
    Temp = db.Column(db.Float, nullable=False)
    Turbidity = db.Column(db.Float, nullable=False)
    DO = db.Column(db.Float, nullable=False)
    BOD = db.Column(db.Float, nullable=False)
    CO2 = db.Column(db.Float, nullable=False)
    pH = db.Column(db.Float, nullable=False)
    Alkalinity = db.Column(db.Float, nullable=False)
    Hardness = db.Column(db.Float, nullable=False)
    Calcium = db.Column(db.Float, nullable=False)
    Ammonia = db.Column(db.Float, nullable=False)
    Nitrite = db.Column(db.Float, nullable=False)
    Phosphorus = db.Column(db.Float, nullable=False)
    H2S = db.Column(db.Float, nullable=False)
    Plankton = db.Column(db.Float, nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "_id": self.id,
            "sensor_data": {
                "Temp": self.Temp,
                "Turbidity": self.Turbidity,
                "DO": self.DO,
                "BOD": self.BOD,
                "CO2": self.CO2,
                "pH": self.pH,
                "Alkalinity": self.Alkalinity,
                "Hardness": self.Hardness,
                "Calcium": self.Calcium,
                "Ammonia": self.Ammonia,
                "Nitrite": self.Nitrite,
                "Phosphorus": self.Phosphorus,
                "H2S": self.H2S,
                "Plankton": self.Plankton,
            },
            "created_at": self.created_at.isoformat(),
        }


class OutputModel(db.Model):
    __tablename__ = "output_model"

    id = db.Column(db.Integer, primary_key=True)
    Temp = db.Column(db.Float, nullable=False)
    Turbidity = db.Column(db.Float, nullable=False)
    DO = db.Column(db.Float, nullable=False)
    BOD = db.Column(db.Float, nullable=False)
    CO2 = db.Column(db.Float, nullable=False)
    pH = db.Column(db.Float, nullable=False)
    Alkalinity = db.Column(db.Float, nullable=False)
    Hardness = db.Column(db.Float, nullable=False)
    Calcium = db.Column(db.Float, nullable=False)
    Ammonia = db.Column(db.Float, nullable=False)
    Nitrite = db.Column(db.Float, nullable=False)
    Phosphorus = db.Column(db.Float, nullable=False)
    H2S = db.Column(db.Float, nullable=False)
    Plankton = db.Column(db.Float, nullable=False)

    quality_label = db.Column(db.Integer, nullable=True)
    quality_name = db.Column(db.String(100), nullable=True)
    solution = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "_id": self.id,
            "sensor_data": {
                "Temp": self.Temp,
                "Turbidity": self.Turbidity,
                "DO": self.DO,
                "BOD": self.BOD,
                "CO2": self.CO2,
                "pH": self.pH,
                "Alkalinity": self.Alkalinity,
                "Hardness": self.Hardness,
                "Calcium": self.Calcium,
                "Ammonia": self.Ammonia,
                "Nitrite": self.Nitrite,
                "Phosphorus": self.Phosphorus,
                "H2S": self.H2S,
                "Plankton": self.Plankton,
            },
            "quality_label": self.quality_label,
            "quality_name": self.quality_name,
            "solution": self.solution,
            "created_at": self.created_at.isoformat(),
        }
