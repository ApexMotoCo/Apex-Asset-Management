import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USERNAME or "noreply@apexingoodcompany.co.uk")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
APP_PUBLIC_URL = os.getenv("APP_PUBLIC_URL", "https://assets.apexingoodcompany.co.uk").rstrip("/")

def send_invitation_email(to_email: str, full_name: str, invite_url: str) -> None:
    if not SMTP_HOST or not SMTP_USERNAME or not SMTP_PASSWORD:
        raise RuntimeError("SMTP is not configured. Set SMTP_HOST, SMTP_USERNAME and SMTP_PASSWORD.")

    msg = EmailMessage()
    msg["Subject"] = "You have been invited to APEX Asset Management"
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    msg.set_content(f"""Hello {full_name},

You have been invited to APEX Asset Management.

Your account has been created with the default location of APEX HUB.

Use the secure invitation link below to set your password and activate your account:

{invite_url}

This invitation expires in 48 hours.

If you were not expecting this invitation, please contact an APEX administrator.

APEX Asset Management
{APP_PUBLIC_URL}
""")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
        if SMTP_USE_TLS:
            server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
