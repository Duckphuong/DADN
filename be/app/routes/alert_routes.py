from flask import Blueprint, request, jsonify
from datetime import datetime, timezone

from app.infrastructure.persistence.mongo.connection import get_mongo_database

alert_bp = Blueprint('alert', __name__, url_prefix="/api/v1/alerts")

@alert_bp.route('', methods=['GET'])
def get_alerts():
    status = request.args.get('status', 'unread')
    try:
        db = get_mongo_database()
        if db is None:
            return jsonify({"error": "MongoDB not connected"}), 500
        coll = db.get_collection("predict_module")
        query = {}
        if status == 'unread':
            query['status'] = 'unread'
        cursor = coll.find(query).sort("created_at", -1).limit(50)
        alerts = []
        for d in cursor:
            raw_date = d.get("created_at")
            # 1. Xử lý hiển thị thời gian (Time Ago)
            # Hàm calculate_time_ago của bạn sẽ nhận raw_date (dù là str hay datetime)
            time_ago_str = calculate_time_ago(raw_date) if raw_date else "N/A"

            # 2. Xử lý định dạng ISO để trả về API
            if isinstance(raw_date, datetime):
                iso_date = raw_date.isoformat()
            elif isinstance(raw_date, str):
                iso_date = raw_date  # Nếu đã là string thì giữ nguyên
            else:
                iso_date = None

            item = {
                "id": str(d["_id"]),
                "wqi_score": d.get("wqi_score"),
                "contamination_risk": d.get("contamination_risk"),
                "message": d.get("message"),
                "status": d.get("status"),
                "time_ago": time_ago_str,
                "created_at": iso_date,
            }
            # Determine level
            wqi = d.get("wqi_score", 100)
            risk = d.get("contamination_risk", "Low Risk")
            if wqi < 30 or risk == "Critical":
                item["level"] = "Critical"
            elif wqi < 50 or risk == "High Risk":
                item["level"] = "Warning"
            else:
                item["level"] = "Info"
            alerts.append(item)
        return jsonify(alerts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@alert_bp.route('/<alert_id>/read', methods=['PUT'])
def mark_read(alert_id):
    try:
        db = get_mongo_database()
        if db is None:
            return jsonify({"error": "MongoDB not connected"}), 500
        from bson import ObjectId
        coll = db.get_collection("predict_module")
        result = coll.update_one({"_id": ObjectId(alert_id)}, {"$set": {"status": "read"}})
        if result.modified_count > 0:
            return jsonify({"message": "Alert marked as read"})
        else:
            return jsonify({"error": "Alert not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def calculate_time_ago(dt):
    if isinstance(dt, str):
        try:
            from dateutil import parser
            dt = parser.parse(dt)
        except ImportError:
            # Nếu không có dateutil, dùng hàm có sẵn của Python cho chuẩn ISO
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))

    # Đảm bảo dt cũng là "timezone-aware" để có thể trừ cho nhau
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # Dùng cách mới để lấy giờ UTC (hết bị gạch ngang)
    now = datetime.now(timezone.utc)
    
    diff = now - dt
    if diff.days > 0:
        return f"{diff.days} day(s) ago"
    seconds = diff.seconds
    if seconds < 60:
        return "Just now"
    if seconds < 3600:
        return f"{seconds // 60} minute(s) ago"
    return f"{seconds // 3600} hour(s) ago"
