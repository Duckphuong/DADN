import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Lock
from bson import ObjectId

from app.infrastructure.persistence.mongo.connection import get_mongo_database


class AlertService:
    SENSOR_ALERT_COOLDOWN = timedelta(hours=2)

    def __init__(self, smtp_server, smtp_port, email, password, enabled=True):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password
        self.enabled = enabled
        self.last_email_time = {}  # Lưu thời gian gửi cảnh báo chất lượng nước của từng sensor
        self.last_sensor_error_time = {}  # Lưu thời gian gửi mail lỗi cuối cùng của từng sensor
        self._sensor_alert_lock = Lock()
        self._pending_sensor_alerts = set()
        self._sensor_alert_executor = ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="sensor-alert",
        )


    def check_and_send_alerts(self):
        """Check predict_module for unprocessed alerts and send emails if needed."""
        if not self.enabled:
            return

        db = get_mongo_database()
        if db is None:
            print("MongoDB not connected")
            return

        coll = db.get_collection("predict_module")

        # Find unprocessed predictions
        cursor = coll.find({"is_email_processed": False})
        for doc in cursor:
            if self._should_send_alert(doc):
                target_email = None
                sensor = None
                try:
                    sensor_id = doc.get("id_sensor") or doc.get("input_sensor_id")
                    if sensor_id:
                        s_id = ObjectId(sensor_id) if isinstance(sensor_id, str) and len(sensor_id) == 24 else sensor_id
                        sensor = db.get_collection("sensor_informations").find_one({"_id": s_id})
                        
                        if sensor and "userId" in sensor:
                            owner_id = sensor.get("userId")
                            o_id = ObjectId(owner_id) if isinstance(owner_id, str) and len(owner_id) == 24 else owner_id
                            user = db.get_collection("users").find_one({"_id": o_id})
                            if user and "email" in user:
                                if user.get("email_notifications_enabled", True):
                                    target_email = user.get("email")
                                else:
                                    print(f"User {owner_id} has disabled email notifications.", flush=True)
                except Exception as e:
                    print(f"Error fetching target email from DB: {e}", flush=True)

                if not target_email:
                    coll.update_one(
                        {"_id": doc["_id"]},
                        {"$set": {"is_email_processed": True}},
                    )
                    continue

                success = self._send_alert_email(doc, target_email, sensor)
                if success:
                    # Update to processed
                    coll.update_one({"_id": doc["_id"]}, {"$set": {"is_email_processed": True}})
                    sensor_id_str = str(doc.get("id_sensor") or doc.get("input_sensor_id"))
                    self.last_email_time[sensor_id_str] = datetime.now(timezone.utc)
                else:
                    print(f"Failed to send alert email for {doc['_id']}.", flush=True)

    def _should_send_alert(self, doc):
        """Determine if an alert should be sent based on prediction data."""
        wqi_score = doc.get("wqi_score", 100)
        contamination_risk = doc.get("contamination_risk", "Low Risk")
        sensor_id_str = str(doc.get("id_sensor") or doc.get("input_sensor_id"))

        # Send alert if WQI < 50 or contamination risk is high
        if wqi_score < 50 or contamination_risk in ["High Risk", "Critical"]:
            # Anti-spam logic per sensor
            last_time = self.last_email_time.get(sensor_id_str)
            if last_time is None:
                return True
                
            time_diff = datetime.now(timezone.utc) - last_time
            # Wait 2 hours to avoid spam, even for critical risks
            if time_diff >= self.SENSOR_ALERT_COOLDOWN:
                return True
                
        return False

    def _send_alert_email(self, doc, target_email, sensor):
        """Send alert email."""
        sensor_name = sensor.get("sensorName", "Unknown") if sensor else "Unknown"
        subject = f"[URGENT ALERT] Sensor Station {sensor_name} - Contamination Risk!"
        html_body = self._generate_email_body(doc, sensor)

        msg = MIMEMultipart()
        msg['From'] = self.email
        msg['To'] = target_email
        msg['Subject'] = subject

        msg.attach(MIMEText(html_body, 'html'))

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
            server.starttls()
            server.login(self.email, self.password)
            text = msg.as_string()
            server.sendmail(self.email, target_email, text)
            server.quit()
            print(f"Alert email sent successfully to {target_email}", flush=True)
            return True
        except Exception as e:
            print(f"Failed to send email: {e}", flush=True)
            return False

    def _generate_email_body(self, doc, sensor):
        """Generate email HTML body from prediction data."""
        wqi_score = doc.get("wqi_score", 0)
        contamination_risk = doc.get("contamination_risk", "")
        forecast_24h = doc.get("forecast_24h", "")
        predicted_wqi = doc.get("predicted_wqi", "")
        confidence = doc.get("confidence", 0)
        message = doc.get("message", "")

        # Sensor info
        sensor_id = doc.get("id_sensor") or doc.get("input_sensor_id") or "No ID"
        sensor_name = sensor.get("sensorName", "Unknown") if sensor else "Unknown"
        
        # Parse location details
        lat, lon = "N/A", "N/A"
        if sensor and "location" in sensor and isinstance(sensor["location"], dict):
            lat = sensor["location"].get("latitude", "N/A")
            lon = sensor["location"].get("longitude", "N/A")

        html_body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-width=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    background-color: #f9f9f9;
                    margin: 0;
                    padding: 0;
                    color: #333333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 40px auto;
                    background-color: #ffffff;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                }}
                .header {{
                    text-align: center;
                    padding: 30px 20px;
                    border-bottom: 1px solid #eeeeee;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                    color: #111111;
                    letter-spacing: -0.5px;
                }}
                .content {{
                    padding: 30px 40px;
                    line-height: 1.5;
                    font-size: 14px;
                }}
                .content p {{
                    margin: 0 0 15px 0;
                }}
                .grey-box {{
                    background-color: #f4f4f5;
                    border-radius: 6px;
                    padding: 20px;
                    margin: 20px 0;
                    font-size: 14px;
                }}
                .grey-box ul {{
                    list-style-type: none;
                    padding: 0;
                    margin: 0;
                }}
                .grey-box li {{
                    margin-bottom: 12px;
                    border-bottom: 1px solid #eaeaea;
                    padding-bottom: 8px;
                }}
                .grey-box li:last-child {{
                    border-bottom: none;
                    margin-bottom: 0;
                    padding-bottom: 0;
                }}
                .grey-box strong {{
                    color: #222222;
                    display: inline-block;
                    width: 140px;
                }}
                .text-danger {{
                    color: #d93025;
                    font-weight: 600;
                }}
                .text-warning {{
                    color: #f29900;
                    font-weight: 600;
                }}
                .signature {{
                    margin-top: 30px;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    background-color: #f9f9f9;
                    font-size: 12px;
                    color: #888888;
                    border-top: 1px solid #eeeeee;
                }}
                .footer a {{
                    color: #1a73e8;
                    text-decoration: none;
                }}
                .footer a:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>WAS Alert System</h1>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p>The WAS (Water Alert System) has detected critical water quality parameters at your station. Our AI engine indicates that immediate attention is required.</p>
                    
                    <div class="grey-box">
                        <ul>
                            <li><strong>Station Name:</strong> {sensor_name}</li>
                            <li><strong>Location (Lat, Lng):</strong> {lat}, {lon}</li>
                            <li><strong>Sensor ID:</strong> {sensor_id}</li>
                            <li><strong>Diagnosis:</strong> {message}</li>
                            <li><strong>WQI Score:</strong> <span class="text-danger">{wqi_score}</span></li>
                            <li><strong>Contamination Risk:</strong> <span class="text-danger">{contamination_risk}</span></li>
                            <li><strong>24h Forecast:</strong> {forecast_24h} (Predicted WQI: {predicted_wqi})</li>
                        </ul>
                    </div>

                    <p>Please inspect your water system immediately and take necessary emergency measures to prevent potential damage.</p>
                    
                    <div class="signature">
                        <p>Best,<br>
                        <strong>The WAS team</strong></p>
                    </div>
                </div>
                <div class="footer">
                    <p>If you have any questions please review the detailed report via the <a href="#">WAS System Dashboard</a>.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html_body




    """
    SENSOR ERROR ALERT
    """
    def submit_sensor_error_alert(self, app, sensor_id: str, error_type: str = "ERROR") -> bool:
        if not self.enabled:
            return False

        cache_key = self._sensor_alert_cache_key(sensor_id, error_type)
        now = datetime.now(timezone.utc)

        with self._sensor_alert_lock:
            if cache_key in self._pending_sensor_alerts:
                return False
            last_sent = self.last_sensor_error_time.get(cache_key)
            if last_sent and (now - last_sent) < self.SENSOR_ALERT_COOLDOWN:
                return False
            self._pending_sensor_alerts.add(cache_key)

        self._sensor_alert_executor.submit(
            self._run_sensor_error_alert_job,
            app,
            str(sensor_id),
            error_type,
            cache_key,
        )
        return True

    def send_sensor_error_alert(self, sensor_id: str, error_type: str = "ERROR") -> bool:
        """
        Send an alert email when a sensor error (all data is 0) or disconnection (offline) is detected.
        
        Args:
            sensor_id (str): ID of the faulty sensor.
            error_type (str): Type of error, e.g., 'ERROR' or 'OFFLINE'.
        
        Returns:
            bool: True if the email was sent successfully, otherwise False.
        """
        if not self.enabled:
            return False

        db = get_mongo_database()
        if db is None:
            print("MongoDB not connected. Cannot send sensor error email.")
            return False
            
        cache_key = self._sensor_alert_cache_key(sensor_id, error_type)
        now = datetime.now(timezone.utc)
        if self._is_sensor_alert_rate_limited(cache_key, now=now):
            return False

        try:
            s_id = ObjectId(sensor_id) if isinstance(sensor_id, str) and len(sensor_id) == 24 else sensor_id
            sensor = db.get_collection("sensor_informations").find_one({"_id": s_id})
            
            target_email = None
            if sensor and "userId" in sensor:
                owner_id = sensor.get("userId")
                o_id = ObjectId(owner_id) if isinstance(owner_id, str) and len(owner_id) == 24 else owner_id
                user = db.get_collection("users").find_one({"_id": o_id})
                if user and "email" in user:
                    if user.get("email_notifications_enabled", True):
                        target_email = user.get("email")
                    else:
                        print(f"User {owner_id} disabled email notifications for sensor error.", flush=True)
            
            if not target_email:
                print(f"No linked email found to notify sensor error (Sensor: {sensor_id}).", flush=True)
                return False

            sensor_name = sensor.get("sensorName", "Unknown") if sensor else "Unknown"
            
            # Initialize Subject
            subject = f"[{error_type.upper()} ALERT] Sensor Station {sensor_name} is facing an issue!"
            html_body = self._generate_sensor_error_email_body(sensor_id, sensor, error_type)

            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = target_email
            msg['Subject'] = subject

            msg.attach(MIMEText(html_body, 'html'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
            server.starttls()
            server.login(self.email, self.password)
            text = msg.as_string()
            server.sendmail(self.email, target_email, text)
            server.quit()
            
            # Update last sent time for this sensor and error type
            self._mark_sensor_alert_sent(cache_key, sent_at=now)
            print(f"Sent {error_type} alert email for sensor to {target_email}", flush=True)
            return True

        except Exception as e:
            print(f"Failed to send sensor alert email: {e}", flush=True)
            return False

    def _run_sensor_error_alert_job(
        self,
        app,
        sensor_id: str,
        error_type: str,
        cache_key: str,
    ) -> None:
        try:
            with app.app_context():
                self.send_sensor_error_alert(sensor_id, error_type)
        except Exception as exc:
            print(f"Failed to dispatch sensor alert task: {exc}", flush=True)
        finally:
            with self._sensor_alert_lock:
                self._pending_sensor_alerts.discard(cache_key)

    @staticmethod
    def _sensor_alert_cache_key(sensor_id: str, error_type: str) -> str:
        return f"{str(sensor_id)}_{error_type}"

    def _is_sensor_alert_rate_limited(
        self,
        cache_key: str,
        *,
        now: datetime,
    ) -> bool:
        with self._sensor_alert_lock:
            last_sent = self.last_sensor_error_time.get(cache_key)
        return bool(last_sent and (now - last_sent) < self.SENSOR_ALERT_COOLDOWN)

    def _mark_sensor_alert_sent(self, cache_key: str, *, sent_at: datetime) -> None:
        with self._sensor_alert_lock:
            self.last_sensor_error_time[cache_key] = sent_at

    def _generate_sensor_error_email_body(self, sensor_id, sensor, error_type):
        """Generate HTML body for hardware error or disconnection alert email."""
        sensor_name = sensor.get("sensorName", "Unknown") if sensor else "Unknown"
        lat, lon = "N/A", "N/A"
        if sensor and "location" in sensor and isinstance(sensor["location"], dict):
            lat = sensor["location"].get("latitude", "N/A")
            lon = sensor["location"].get("longitude", "N/A")

        if error_type == "ERROR":
            error_description = "The sensor is sending invalid data (all parameters are 0). This may be due to a hardware failure or a short circuit."
        else:
            error_description = "The sensor station has stopped sending data to the system for a long time (Disconnected). This could be due to low battery, power outage, or network configuration loss."

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-width=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                    background-color: #f9f9f9;
                    margin: 0; padding: 0; color: #333;
                }}
                .container {{
                    max-width: 600px; margin: 40px auto; background-color: #fff;
                    border-radius: 8px; padding: 30px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                }}
                .header {{ border-bottom: 1px solid #eee; padding-bottom: 20px; text-align: center; }}
                .header h1 {{ color: #d93025; margin: 0; font-size: 24px; }}
                .content {{ padding: 20px 0; line-height: 1.6; font-size: 15px; }}
                .box {{
                    background-color: #f4f4f5; border-radius: 6px; padding: 20px; margin: 20px 0;
                }}
                .box ul {{ padding: 0; margin: 0; list-style: none; }}
                .box li {{ padding: 10px 0; border-bottom: 1px solid #eaeaea; }}
                .box li:last-child {{ border-bottom: none; }}
                .box strong {{ display: inline-block; width: 140px; color: #222; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Sensor Issue Detected</h1>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p>The WAS has detected an issue with one of your sensor stations.</p>
                    <p><strong>Issue Type: <span style="color: #d93025;">{error_type}</span></strong></p>
                    <p>{error_description}</p>
                    
                    <div class="box">
                        <ul>
                            <li><strong>Station Name:</strong> {sensor_name}</li>
                            <li><strong>Station ID:</strong> {sensor_id}</li>
                            <li><strong>Location (Lat, Lng):</strong> {lat}, {lon}</li>
                        </ul>
                    </div>

                    <p>Please inspect the hardware or power supply of the sensor station immediately to resolve the issue.</p>
                    <p>Best regards,<br><strong>The WAS Operations Team</strong></p>
                </div>
            </div>
        </body>
        </html>
        """
