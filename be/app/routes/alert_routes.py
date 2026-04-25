from flask import Blueprint, request, jsonify, g
from datetime import datetime, timezone
from bson import ObjectId

from app.infrastructure.persistence.mongo.connection import get_mongo_database
from app.presentation.http.middleware.auth_middleware import jwt_required

alert_bp = Blueprint('alert', __name__, url_prefix="/api/v1/alerts")

@alert_bp.route('', methods=['GET'])
@jwt_required
def get_alerts():
    status = request.args.get('status', 'unread')
    
    try:
        db = get_mongo_database()
        if db is None:
            return jsonify({"error": "MongoDB not connected"}), 500
            
        coll = db.get_collection("predict_module")
        query = {}
        
        # Security: Chỉ người dùng đăng nhập mới được gọi
        current_user_id = g.current_user.id

        try:
            # Tìm các sensor thuộc sở hữu của current_user
            u_id = ObjectId(current_user_id) if isinstance(current_user_id, str) and len(current_user_id) == 24 else current_user_id
            sensors_cursor = db.get_collection("sensor_informations").find({"userId": u_id})
            sensor_ids = [str(sensor["_id"]) for sensor in sensors_cursor]
            
            if not sensor_ids:
                return jsonify([]) # Trả về rỗng nếu user không có trạm nào
                
            # Tạo cú pháp để tìm cả ObjectId và chuỗi
            query["$or"] = [
                {"id_sensor": {"$in": sensor_ids}},
                {"id_sensor": {"$in": [ObjectId(s) for s in sensor_ids if len(s)==24]}}
            ]
        except Exception as e:
            print(f"Error filtering by user_id: {e}")
            return jsonify({"error": "Internal server error during fetching sensors"}), 500

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
@jwt_required
def mark_read(alert_id):
    try:
        db = get_mongo_database()
        if db is None:
            return jsonify({"error": "MongoDB not connected"}), 500
            
        coll = db.get_collection("predict_module")
        current_user_id = g.current_user.id
        u_id = ObjectId(current_user_id) if isinstance(current_user_id, str) and len(current_user_id) == 24 else current_user_id

        # Verify Quyền Sở Hữu
        alert = coll.find_one({"_id": ObjectId(alert_id)})
        if not alert:
            return jsonify({"error": "Alert not found"}), 404
            
        sensor_id = alert.get("id_sensor")
        if not sensor_id:
            return jsonify({"error": "Alert is missing corresponding sensor"}), 400
            
        s_id = ObjectId(sensor_id) if isinstance(sensor_id, str) and len(sensor_id) == 24 else sensor_id
        
        sensor = db.get_collection("sensor_informations").find_one({"_id": s_id, "userId": u_id})
        if not sensor:
            return jsonify({"error": "Forbidden: You don't own the sensor connected to this alert"}), 403

        # Owner hợp lệ, tiến hành update sang Trạng thái Read
        result = coll.update_one({"_id": ObjectId(alert_id)}, {"$set": {"status": "read"}})
        if result.modified_count > 0:
            return jsonify({"message": "Alert marked as read"})
        else:
            return jsonify({"message": "Alert was already marked as read"}), 200
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

@alert_bp.route('/settings/email', methods=['GET'])
@jwt_required
def get_email_alerts_setting():
    try:
        db = get_mongo_database()
        if db is None:
            return jsonify({"error": "MongoDB not connected"}), 500
            
        current_user_id = g.current_user.id
        u_id = ObjectId(current_user_id) if isinstance(current_user_id, str) and len(current_user_id) == 24 else current_user_id
        
        user = db.get_collection("users").find_one({"_id": u_id})
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        # Trả về True nếu trường này chưa tồn tại (mặc định là bật)
        enabled = user.get("email_notifications_enabled", True)
        
        return jsonify({"enabled": enabled}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@alert_bp.route('/settings/email', methods=['PUT'])
@jwt_required
def toggle_email_alerts():
    try:
        db = get_mongo_database()
        if db is None:
            return jsonify({"error": "MongoDB not connected"}), 500
        
        data = request.get_json(silent=True) or {}
        if "enabled" not in data:
            return jsonify({"error": "Missing 'enabled' field"}), 400
            
        enabled = bool(data["enabled"])
        
        current_user_id = g.current_user.id
        u_id = ObjectId(current_user_id) if isinstance(current_user_id, str) and len(current_user_id) == 24 else current_user_id
        
        db.get_collection("users").update_one(
            {"_id": u_id},
            {"$set": {"email_notifications_enabled": enabled}}
        )
        
        return jsonify({"message": "Email alert settings updated successfully", "enabled": enabled}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
