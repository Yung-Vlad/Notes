from fastapi import HTTPException, status

import smtplib, os
from email.mime.text import MIMEText
from dotenv import load_dotenv


load_dotenv()
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_TOKEN = os.getenv("EMAIL_TOKEN")

smtp_server = "smtp.gmail.com"
smtp_port = 465


def notify(receiver: str, text: str) -> None:
    try:

        message = MIMEText(text)
        message["Subject"] = "NotesAPI"
        message["To"] = receiver

        # Securely sending
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(EMAIL_ADDRESS, EMAIL_TOKEN)
            server.send_message(message)

    except smtplib.SMTPConnectError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.smtp_error)
