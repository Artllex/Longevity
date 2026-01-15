import os
import smtplib
from email.message import EmailMessage


def main():
    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASS"]

    msg = EmailMessage()
    msg["From"] = smtp_user
    msg["To"] = smtp_user  # wysyłasz do siebie
    msg["Subject"] = "test"
    msg.set_content("test")

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)

    print("✅ Test mail sent successfully")


if __name__ == "__main__":
    main()
