import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import time

from app.infrastructure.persistence.mongo.connection import get_mongo_database


class AlertService:
    def __init__(self, smtp_server, smtp_port, email, password, alert_email_to):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password
        self.alert_email_to = alert_email_to
        self.last_email_time = None  # Track last email sent time

    def check_and_send_alerts(self):
        """Check predict_module for unprocessed alerts and send emails if needed."""
        db = get_mongo_database()
        if db is None:
            print("MongoDB not connected")
            return

        coll = db.get_collection("predict_module")
        # Find unprocessed predictions
        cursor = coll.find({"is_email_processed": False})
        for doc in cursor:
            if self._should_send_alert(doc):
                target_email = self.alert_email_to # Fallback nếu không tìm thấy
                try:
                    sensor_id = doc.get("id_sensor") or doc.get("input_sensor_id")
                    if sensor_id:
                        from bson import ObjectId
                        
                        s_id = ObjectId(sensor_id) if isinstance(sensor_id, str) and len(sensor_id) == 24 else sensor_id
                        sensor = db.get_collection("sensor_informations").find_one({"_id": s_id})
                        
                        if sensor and "userId" in sensor:
                            owner_id = sensor.get("userId")
                            o_id = ObjectId(owner_id) if isinstance(owner_id, str) and len(owner_id) == 24 else owner_id
                            user = db.get_collection("users").find_one({"_id": o_id})
                            
                            if user and "email" in user:
                                target_email = user.get("email")
                except Exception as e:
                    print(f"Error fetching target email from DB: {e}")

                self._send_alert_email(doc, target_email)
                # Update to processed
                coll.update_one({"_id": doc["_id"]}, {"$set": {"is_email_processed": True}})
                self.last_email_time = datetime.utcnow()

    def _should_send_alert(self, doc):
        """Determine if an alert should be sent based on prediction data."""
        wqi_score = doc.get("wqi_score", 100)
        contamination_risk = doc.get("contamination_risk", "Low Risk")

        # Send alert if WQI < 50 or contamination risk is high
        if wqi_score < 50 or contamination_risk in ["High Risk", "Critical"]:
            # Anti-spam logic
            if self.last_email_time is None:
                return True
            time_diff = datetime.utcnow() - self.last_email_time
            if contamination_risk in ["High Risk", "Critical"]:
                # Send immediately for critical
                return True
            else:
                # Wait 2 hours for non-critical
                return time_diff >= timedelta(hours=2)
        return False

    def _send_alert_email(self, doc, target_email):
        """Send alert email."""
        subject = "Water Quality Alert"
        body = self._generate_email_body(doc)

        msg = MIMEMultipart()
        msg['From'] = self.email
        msg['To'] = target_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.password)
            text = msg.as_string()
            server.sendmail(self.email, target_email, text)
            server.quit()
            print(f"Alert email sent successfully to {target_email}")
        except Exception as e:
            print(f"Failed to send email: {e}")

    def _generate_email_body(self, doc):
        """Generate email body from prediction data."""
        wqi_score = doc.get("wqi_score", 0)
        contamination_risk = doc.get("contamination_risk", "")
        forecast_24h = doc.get("forecast_24h", "")
        predicted_wqi = doc.get("predicted_wqi", "")
        confidence = doc.get("confidence", 0)
        message = doc.get("message", "")

        body = f"""
        Water Quality Alert

        Current Status:
        - WQI Score: {wqi_score}
        - Contamination Risk: {contamination_risk}
        - 24h Forecast: {forecast_24h}
        - Predicted WQI Range: {predicted_wqi}
        - Confidence: {confidence}%

        Message: {message}

        Please take immediate action if necessary.

        This is an automated alert from the Water Quality Monitoring System.
        """
        return body.strip()