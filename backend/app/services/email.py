"""Email service — sends transactional emails via the Mailgun HTTP API."""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def _is_email_enabled() -> bool:
    """Return True if Mailgun is configured and we're not using a test database."""
    return bool(settings.mailgun_api_key) and not settings.database_url.startswith("sqlite")


async def send_password_reset_email(to_email: str, reset_token: str) -> None:
    """Send a password reset email with a link containing the reset token.

    In test/dev mode (SQLite DB or no API key), the reset link is logged instead.
    """
    reset_link = f"{settings.frontend_url}/#/reset-password?token={reset_token}"

    if not _is_email_enabled():
        logger.info(
            "\n========================================"
            "\nPASSWORD RESET LINK (email disabled)"
            "\nTo: %s"
            "\nLink: %s"
            "\n========================================",
            to_email,
            reset_link,
        )
        return

    text_body = (
        "You requested a password reset for your Steps Challenge account.\n\n"
        f"Click the link below to reset your password:\n\n{reset_link}\n\n"
        "This link will expire in 1 hour.\n\n"
        "If you did not request this, please ignore this email."
    )
    html_body = (
        "<p>You requested a password reset for your Steps Challenge account.</p>"
        f'<p><a href="{reset_link}">Click here to reset your password</a></p>'
        "<p>This link will expire in 1 hour.</p>"
        "<p>If you did not request this, please ignore this email.</p>"
    )

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://api.mailgun.net/v3/{settings.mailgun_domain}/messages",
                auth=("api", settings.mailgun_api_key),
                data={
                    "from": settings.mail_from_address,
                    "to": [to_email],
                    "subject": "Steps Challenge — Password Reset",
                    "text": text_body,
                    "html": html_body,
                },
            )
            resp.raise_for_status()
            logger.info("Password reset email sent to %s", to_email)
    except httpx.HTTPError:
        logger.exception("Failed to send password reset email to %s", to_email)
        # Don't raise — the caller already returns a generic success message
