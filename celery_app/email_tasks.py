
import ssl
import smtplib
import logging

from email.message import EmailMessage

from celery_app.celery_config import celery_app
from config.settings import settings

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(
        smtplib.SMTPServerDisconnected,
        smtplib.SMTPConnectError,
        TimeoutError,
        ConnectionError,
        OSError
    ),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    retry_jitter=True
)
def send_welcome_email(self, email: str, name: str):
    message = EmailMessage()

    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = email
    message["Subject"] = "Welcome to E-Commerce Order Management System"

    message.set_content(
        f"Hello {name},\n\n"
        "Welcome to our E-Commerce Order Management System!\n\n"
        "Your account has been registered successfully.\n"
        "You can now log in, explore products, "
        "add items to your cart and place orders.\n\n"
        "Thank you for joining us!\n\n"
        "Best regards,\n"
        "E-Commerce Team"
    )

    context = ssl.create_default_context()

    with smtplib.SMTP(
        settings.SMTP_HOST,
        settings.SMTP_PORT,
        timeout=20
    ) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(
            settings.SMTP_USER,
            settings.SMTP_PASSWORD
        )
        server.send_message(message)

    logger.info("Welcome email submitted for %s", email)

    return {"message": "Welcome email submitted"}
