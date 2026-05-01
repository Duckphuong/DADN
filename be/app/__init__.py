def create_app():
    from apscheduler.schedulers.background import BackgroundScheduler
    from flask import Flask, jsonify
    from flask_cors import CORS

    from app.bootstrap.container import CONTAINER_EXTENSION_KEY, build_container
    from app.config import Config
    from app.infrastructure.persistence.mongo.connection import get_mongo_state, init_mongo
    from app.presentation.http.routes.analytics_routes import analytics_bp
    from app.presentation.http.routes.auth_routes import auth_bp
    from app.presentation.http.routes.sensor_data_routes import sensor_data_bp
    from app.presentation.http.routes.sensor_station_routes import sensor_station_bp
    from app.routes.alert_routes import alert_bp
    from app.routes.prediction_routes import prediction_bp
    from app.services.alert_service import AlertService
    from app.services.sensor_health_service import SensorHealthService

    app = Flask(__name__)
    app.config.from_object(Config)

    # CORS(app)  # Enable CORS for all routes
    CORS(app, resources={r"/*": {"origins": "*"}}, 
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])

    init_mongo(app)
    app.extensions[CONTAINER_EXTENSION_KEY] = build_container(app.config)

    app.register_blueprint(auth_bp)
    app.register_blueprint(sensor_station_bp)
    app.register_blueprint(sensor_data_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(alert_bp)
    
    # Start alert service scheduler
    alert_service = AlertService(
        smtp_server=app.config['SMTP_SERVER'],
        smtp_port=app.config['SMTP_PORT'],
        email=app.config['EMAIL'],
        password=app.config['PASSWORD'],
        enabled=app.config['ALERT_EMAIL_ENABLED'],
    )
    
    app.extensions['alert_service'] = alert_service
    
    def scheduled_task():
        with app.app_context():
            alert_service.check_and_send_alerts()

    scheduler = BackgroundScheduler(
        job_defaults={
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 300,
        }
    )
    scheduler.add_job(
        func=scheduled_task,
        trigger="interval",
        minutes=1,
        id="alert_check",
        replace_existing=True,
    )
    scheduler.start()

    sensor_health = SensorHealthService()
    def sensor_health_task():
        with app.app_context():
            sensor_health.mark_offline_sensors()

    scheduler.add_job(
        func=sensor_health_task,
        trigger="interval",
        minutes=60*24,
        id="sensor_health_check",
        replace_existing=True,
    )

    @app.route("/")
    def home():
        return {
            "status": "ok",
            "message": "Backend is running"
    }
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
