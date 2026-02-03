"""Email service for sending notifications and reset links."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger()


def send_reset_email(email: str, reset_token: str) -> None:
    """Send API key reset email with reset token.

    In development (RESET_METHOD=console), logs to console.
    In production (RESET_METHOD=email), sends via SMTP.

    Args:
        email: User's email address
        reset_token: Plain reset token to include in email
    """
    reset_link = f"{settings.PROJECT_NAME.lower()}://reset?token={reset_token}"

    if settings.RESET_METHOD == "console":
        _log_reset_email(email, reset_token, reset_link)
        return

    _send_smtp_email(email, reset_token, reset_link)


def _log_reset_email(email: str, reset_token: str, reset_link: str) -> None:
    """Log reset details to console (development mode).

    Args:
        email: User's email address
        reset_token: Plain reset token
        reset_link: Full reset link
    """
    logger.info(
        "API Key Reset Request",
        email=email,
        reset_token=reset_token,
        reset_link=reset_link,
    )
    print("\n" + "=" * 60)
    print("SECAPI - API KEY RESET")
    print("=" * 60)
    print(f"Email: {email}")
    print(f"Reset Token: {reset_token}")
    print(f"Reset Link: {reset_link}")
    print("=" * 60 + "\n")


def _send_smtp_email(email: str, reset_token: str, reset_link: str) -> None:
    """Send reset email via SMTP (production mode).

    Args:
        email: User's email address
        reset_token: Plain reset token
        reset_link: Full reset link

    Raises:
        smtplib.SMTPException: If email sending fails
    """
    try:
        msg = EmailMessage()
        msg["From"] = settings.SMTP_FROM
        msg["To"] = email
        msg["Subject"] = f"{settings.PROJECT_NAME} - API Key Reset Request"

        body = _get_email_body(reset_token, reset_link)
        msg.set_content(body, subtype="html")

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(
            "Reset email sent successfully",
            email=email,
        )

    except smtplib.SMTPException as e:
        logger.error(
            "Failed to send reset email",
            email=email,
            error=str(e),
        )
        raise


def _get_email_body(reset_token: str, reset_link: str) -> str:
    """Generate HTML email body for reset email.

    Args:
        reset_token: Plain reset token
        reset_link: Full reset link

    Returns:
        HTML email body
    """
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #1a1a1a; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px 20px; background: #f5f5f5; }}
        .code {{ background: #fff; padding: 15px; border: 1px solid #ddd;
                 font-family: monospace; font-size: 14px; word-break: break-all; }}
        .button {{ display: inline-block; padding: 12px 30px; background: #2563eb;
                   color: white; text-decoration: none; border-radius: 6px; }}
        .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{settings.PROJECT_NAME}</h1>
        </div>
        <div class="content">
            <h2>API Key Reset Request</h2>
            <p>You requested to reset your API key. Use the token below to complete the reset:</p>
            <div class="code">{reset_token}</div>
            <p>Or click the button below:</p>
            <p><a href="{reset_link}" class="button">Reset API Key</a></p>
            <p><strong>This token expires in {settings.RESET_TOKEN_EXPIRY_MINUTES} minutes.</strong></p>
            <p>If you didn't request this reset, please ignore this email.</p>
        </div>
        <div class="footer">
            <p>This is an automated message from {settings.PROJECT_NAME}</p>
        </div>
    </div>
</body>
</html>
"""
