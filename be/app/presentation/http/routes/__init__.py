from app.presentation.http.routes.analytics_routes import analytics_bp
from app.presentation.http.routes.auth_routes import auth_bp
from app.presentation.http.routes.sensor_data_routes import sensor_data_bp
from app.presentation.http.routes.sensor_station_routes import sensor_station_bp

__all__ = ["analytics_bp", "auth_bp", "sensor_data_bp", "sensor_station_bp"]
