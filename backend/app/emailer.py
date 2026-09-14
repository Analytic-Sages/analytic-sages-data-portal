"""Dev-friendly email sender (logs tokens when SMTP is not configured)."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger("as_portal.email")


def frontend_origin() -> str:
    return os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173").rstrip("/")


def send_verification_email(email: str, token: str) -> None:
    link = f"{frontend_origin()}/verify-email?token={token}"
    _send(
        email,
        "Verify your Analytic Sages Data Portal account",
        f"Verify your email to finish joining early access:\n\n{link}\n",
    )


def send_approval_email(email: str) -> None:
    link = f"{frontend_origin()}/query"
    _send(
        email,
        "Your Analytic Sages Data Portal access is ready",
        (
            "You're in.\n\n"
            "Your access to Query Studio has been approved.\n"
            "You can now run SQL against curated blockchain datasets, "
            "analyze results, create visualizations, and build dashboards.\n\n"
            f"Open Query Studio: {link}\n"
        ),
    )


def send_password_reset_email(email: str, token: str) -> None:
    link = f"{frontend_origin()}/reset-password?token={token}"
    _send(
        email,
        "Reset your Analytic Sages password",
        f"Reset your password:\n\n{link}\n",
    )


def _send(to_email: str, subject: str, body: str) -> None:
    # Production can wire Resend/SMTP later; never block signup on email.
    logger.info("EMAIL to=%s subject=%s\n%s", to_email, subject, body)
    print(f"[as-portal-email] to={to_email} subject={subject}\n{body}", flush=True)
