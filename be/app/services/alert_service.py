import smtplib
from email.message import EmailMessage

from flask import current_app


class AlertServiceError(Exception):
    pass


class AlertService:
    @staticmethod
    def send_warning_email(device_id, value):
        sender_email = current_app.config.get("EMAIL")
        sender_password = current_app.config.get("PASSWORD")
        recipient_email = current_app.config.get("ALERT_EMAIL_TO", sender_email)

        if (
            not sender_email
            or not sender_password
            or sender_email == "your_email@gmail.com"
            or sender_password == "app_password"
        ):
            raise AlertServiceError("Email credentials are not configured")

        message = EmailMessage()
        message["Subject"] = "Water Quality Alert"
        message["From"] = sender_email
        message["To"] = recipient_email
        message.set_content(
            "Warning! Sensor value exceeded threshold.\n\n"
            f"Device: {device_id}\n"
            f"Value: {AlertService._serialize_value(value)}"
        )

        try:
            with smtplib.SMTP(
                current_app.config["SMTP_SERVER"],
                current_app.config["SMTP_PORT"],
            ) as smtp:
                smtp.starttls()
                smtp.login(sender_email, sender_password)
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException) as exc:
            raise AlertServiceError("Failed to send alert email") from exc

    @staticmethod
    def _serialize_value(value):
        return int(value) if float(value).is_integer() else value
