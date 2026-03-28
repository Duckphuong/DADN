from flask import Flask, jsonify
from flask_cors import CORS

from app.bootstrap.container import CONTAINER_EXTENSION_KEY, build_container
from app.config import Config
from app.infrastructure.persistence.mongo.connection import get_mongo_state, init_mongo
from app.presentation.http.routes.auth_routes import auth_bp
from app.presentation.http.routes.sensor_station_routes import sensor_station_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)  # Enable CORS for all routes

    init_mongo(app)
    app.extensions[CONTAINER_EXTENSION_KEY] = build_container(app.config)

    app.register_blueprint(auth_bp)
    app.register_blueprint(sensor_station_bp)

    @app.get("/health")
    def health_check():
        mongo_state = get_mongo_state()
        status = (
            "ok"
            if mongo_state.get("connected") or not mongo_state.get("configured")
            else "degraded"
        )
        return jsonify({"status": status, "mongo": mongo_state}), 200

    return app
