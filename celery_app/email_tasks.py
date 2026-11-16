
import os
import ssl
import smtplib
import logging

from pathlib import Path
from email.message import EmailMessage

from dotenv import load_dotenv
from pydantic import EmailStr, TypeAdapter, ValidationError

from celery_app.celery_config import celery_app


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(
        smtplib.SMTPServerDisconnected,
        smtplib.SMTPConnectError,
        smtplib.SMTPServerDisconnected,
        TimeoutError,
        ConnectionError,
        OSError
    ),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    retry_jitter=True
)
def send_welcome_email(self, email: str, name: str):
    try:
        email = str(TypeAdapter(EmailStr).validate_python(email))
    except ValidationError:
        logger.error(
            "Invalid welcome email recipient: %s",
            email
        )
        raise ValueError("Invalid recipient email address")

    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.environ["SMTP_USER"]
    smtp_password = os.environ["SMTP_PASSWORD"]
    sender_email = os.environ["SMTP_FROM_EMAIL"]

    message = EmailMessage()
    message["From"] = sender_email
    message["To"] = email
    message["Subject"] = "Welcome to E-Commerce Order Management System"

    message.set_content(
        f"Hello {name},\n\n"
        "Welcome to our E-Commerce Order Management System!\n\n"
        "Your account has been registered successfully.\n"
        "You can now log in, explore products, "
        "add items to your cart, and place orders.\n\n"
        "Thank you for joining us!\n\n"
        "Best regards,\n"
        "E-Commerce Team"
    )

    context = ssl.create_default_context()

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(
                smtp_host,
                smtp_port,
                timeout=20,
                context=context
            ) as server:
                server.login(smtp_user, smtp_password)
                server.send_message(message)

        else:
            with smtplib.SMTP(
                smtp_host,
                smtp_port,
                timeout=20
            ) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(smtp_user, smtp_password)
                server.send_message(message)

    except smtplib.SMTPException:
        logger.exception(
            "SMTP error sending welcome email to %s",
            email
        )
        raise

    logger.info(
        "Welcome email successfully submitted for %s",
        email
    )

    return {
        "message": "Welcome email submitted",
        "email": email
    }
