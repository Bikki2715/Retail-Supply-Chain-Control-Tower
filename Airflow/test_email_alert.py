
import os
import smtplib
from email.message import EmailMessage

msg = EmailMessage()
msg["Subject"] = "Retail Supply Chain - Test Alert"
msg["From"] = os.environ["SMTP_USER"]
msg["To"] = os.environ["ALERT_EMAIL_TO"]
msg.set_content(
    "Success! Gmail alerts are connected to the "
    "Retail Supply Chain Control Tower."
)

with smtplib.SMTP(
    os.environ["SMTP_HOST"],
    int(os.environ["SMTP_PORT"])
) as server:
    server.starttls()
    server.login(
        os.environ["SMTP_USER"],
        os.environ["SMTP_PASSWORD"]
    )
    server.send_message(msg)

print("TEST EMAIL SENT SUCCESSFULLY")
