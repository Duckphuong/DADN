import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import time
from bson import ObjectId

from app.infrastructure.persistence.mongo.connection import get_mongo_database


class AlertService:
    def __init__(self, smtp_server, smtp_port, email, password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password
        self.last_email_time = None  
        self.last_sensor_error_time = {}  # Lưu thời gian gửi mail lỗi cuối cùng của từng sensor


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
                                target_email = user.get("email")
                except Exception as e:
                    print(f"Error fetching target email from DB: {e}", flush=True)

                if not target_email:
                    print(f"There is no valid target email for alert {doc['_id']}.", flush=True)
                    continue

                success = self._send_alert_email(doc, target_email, sensor)
                if success:
                    # Update to processed
                    coll.update_one({"_id": doc["_id"]}, {"$set": {"is_email_processed": True}})
                    self.last_email_time = datetime.utcnow()
                else:
                    print(f"Failed to send alert email for {doc['_id']}.", flush=True)

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
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
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
    def send_sensor_error_alert(self, sensor_id: str, error_type: str = "ERROR") -> bool:
        """
        Send an alert email when a sensor error (all data is 0) or disconnection (offline) is detected.
        
        Args:
            sensor_id (str): ID of the faulty sensor.
            error_type (str): Type of error, e.g., 'ERROR' or 'OFFLINE'.
        
        Returns:
            bool: True if the email was sent successfully, otherwise False.
        """
        db = get_mongo_database()
        if db is None:
            print("MongoDB not connected. Cannot send sensor error email.")
            return False
            
        # Avoid spam mail, send only 1 email per sensor per error type within 2 hours
        cache_key = f"{str(sensor_id)}_{error_type}"
        now = datetime.utcnow()
        last_sent = self.last_sensor_error_time.get(cache_key)
        if last_sent and (now - last_sent) < timedelta(hours=2):
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
                    target_email = user.get("email")
            
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

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.password)
            text = msg.as_string()
            server.sendmail(self.email, target_email, text)
            server.quit()
            
            # Update last sent time for this sensor and error type
            self.last_sensor_error_time[cache_key] = now
            print(f"Sent {error_type} alert email for sensor to {target_email}", flush=True)
            return True

        except Exception as e:
            print(f"Failed to send sensor alert email: {e}", flush=True)
            return False

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