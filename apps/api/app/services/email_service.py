"""Async email service for CuraMind notifications."""
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import settings

logger = logging.getLogger(__name__)


async def _send(to: str, subject: str, html_body: str) -> None:
    """Internal helper — silently logs on failure so registration never breaks."""
    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        logger.info("Email not configured — skipping send to %s: %s", to, subject)
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME or None,
            password=settings.SMTP_PASSWORD or None,
            use_tls=settings.SMTP_USE_TLS,
        )
        logger.info("Email sent to %s: %s", to, subject)
    except Exception as exc:
        logger.warning("Failed to send email to %s: %s", to, exc)


_BRAND_HEADER = """
<div style="background:#1e3a6b;padding:20px 32px;border-radius:8px 8px 0 0;">
  <span style="color:white;font-size:22px;font-weight:700;letter-spacing:1px;">CuraMind</span>
  <span style="color:#93c5fd;font-size:12px;display:block;margin-top:2px;">Empowering Evidence-Based Care</span>
</div>
"""

_BRAND_FOOTER = """
<div style="background:#f1f5f9;padding:12px 32px;border-radius:0 0 8px 8px;font-size:11px;color:#94a3b8;text-align:center;">
  &copy; CuraMind. All rights reserved.
</div>
"""


def _wrap(body: str) -> str:
    return f"""
<html><body style="margin:0;padding:0;font-family:Arial,sans-serif;background:#f8fafc;">
  <div style="max-width:540px;margin:40px auto;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
    {_BRAND_HEADER}
    <div style="background:white;padding:28px 32px;">
      {body}
    </div>
    {_BRAND_FOOTER}
  </div>
</body></html>
"""


async def send_student_registration_confirmation(email: str, username: str) -> None:
    body = f"""
    <p style="color:#1e3a6b;font-size:18px;font-weight:600;">Welcome to CuraMind, {username}!</p>
    <p style="color:#475569;">Your student account has been created successfully.</p>
    <p style="color:#475569;">You can now <strong>sign in</strong> using your registered email and password to access evidence-based psychology knowledge bases.</p>
    <div style="margin:20px 0;padding:16px;background:#eff6ff;border-radius:6px;border-left:4px solid #2563eb;">
      <p style="margin:0;color:#1e40af;font-size:13px;">As a student, you can read and download articles from the knowledge base.</p>
    </div>
    <p style="color:#94a3b8;font-size:12px;margin-top:24px;">If you did not create this account, please ignore this email.</p>
    """
    await _send(email, "Welcome to CuraMind — Account Created", _wrap(body))


async def send_pending_approval_notification(email: str, username: str, role: str) -> None:
    body = f"""
    <p style="color:#1e3a6b;font-size:18px;font-weight:600;">Registration Received, {username}</p>
    <p style="color:#475569;">Thank you for registering on <strong>CuraMind</strong>.</p>
    <p style="color:#475569;">Your request for the <strong>{role.replace('_', ' ').title()}</strong> role is currently <strong>pending admin approval</strong>.</p>
    <div style="margin:20px 0;padding:16px;background:#fef3c7;border-radius:6px;border-left:4px solid #d97706;">
      <p style="margin:0;color:#92400e;font-size:13px;">You will receive another email once your account is approved. Until then, you can sign in with student-level access.</p>
    </div>
    <p style="color:#94a3b8;font-size:12px;margin-top:24px;">If you did not create this account, please ignore this email.</p>
    """
    await _send(email, "CuraMind — Role Approval Pending", _wrap(body))


async def send_admin_new_user_notification(admin_email: str, username: str, user_email: str, role: str) -> None:
    body = f"""
    <p style="color:#1e3a6b;font-size:18px;font-weight:600;">New User Pending Approval</p>
    <p style="color:#475569;">A new user has registered and is requesting the <strong>{role.replace('_', ' ').title()}</strong> role.</p>
    <table style="width:100%;border-collapse:collapse;margin:16px 0;">
      <tr><td style="padding:8px;color:#64748b;font-size:13px;">Username</td><td style="padding:8px;font-weight:600;color:#1e293b;">{username}</td></tr>
      <tr style="background:#f8fafc;"><td style="padding:8px;color:#64748b;font-size:13px;">Email</td><td style="padding:8px;font-weight:600;color:#1e293b;">{user_email}</td></tr>
      <tr><td style="padding:8px;color:#64748b;font-size:13px;">Requested Role</td><td style="padding:8px;font-weight:600;color:#1e293b;">{role.replace('_', ' ').title()}</td></tr>
    </table>
    <p style="color:#475569;">Please log in to the <strong>CuraMind Admin Panel</strong> to review and approve or reject this request.</p>
    """
    await _send(admin_email, f"CuraMind — New {role.replace('_', ' ').title()} Pending Approval", _wrap(body))


async def send_role_approved_notification(email: str, username: str, role: str) -> None:
    body = f"""
    <p style="color:#1e3a6b;font-size:18px;font-weight:600;">Your Account Has Been Approved!</p>
    <p style="color:#475569;">Congratulations, <strong>{username}</strong>!</p>
    <p style="color:#475569;">Your <strong>CuraMind</strong> account has been approved with the role: <strong>{role.replace('_', ' ').title()}</strong>.</p>
    <div style="margin:20px 0;padding:16px;background:#dcfce7;border-radius:6px;border-left:4px solid #16a34a;">
      <p style="margin:0;color:#166534;font-size:13px;">You now have access to all features available to your role. Sign in to get started.</p>
    </div>
    """
    await _send(email, "CuraMind — Account Approved", _wrap(body))


async def send_role_rejected_notification(email: str, username: str, role: str) -> None:
    body = f"""
    <p style="color:#1e3a6b;font-size:18px;font-weight:600;">Role Request Update</p>
    <p style="color:#475569;">Hello <strong>{username}</strong>,</p>
    <p style="color:#475569;">Your request for the <strong>{role.replace('_', ' ').title()}</strong> role on CuraMind could not be approved at this time.</p>
    <p style="color:#475569;">Your account remains active with <strong>Student</strong> access. If you believe this is an error, please contact support.</p>
    """
    await _send(email, "CuraMind — Role Request Update", _wrap(body))


async def send_new_articles_notification(email: str, username: str, count: int) -> None:
    body = f"""
    <p style="color:#1e3a6b;font-size:18px;font-weight:600;">New Content Available</p>
    <p style="color:#475569;">Hello <strong>{username}</strong>,</p>
    <p style="color:#475569;"><strong>{count} new article(s)</strong> have been approved and are now available in the CuraMind knowledge base.</p>
    <p style="color:#475569;">Sign in to explore the latest evidence-based content.</p>
    """
    await _send(email, f"CuraMind — {count} New Article(s) Available", _wrap(body))
