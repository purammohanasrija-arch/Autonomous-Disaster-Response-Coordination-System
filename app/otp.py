"""
OTP system — 6-digit code with 10-minute expiry, delivered via Gmail.
"""
import os, random, time, smtplib, logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger  = logging.getLogger(__name__)
_store: dict = {}
OTP_TTL = 600  # 10 minutes


def _make_otp(username: str) -> str:
    otp = str(random.randint(100000, 999999))
    _store[username] = {'otp': otp, 'expires_at': time.time() + OTP_TTL, 'attempts': 0}
    return otp


def verify_otp(username: str, otp: str) -> bool:
    record = _store.get(username)
    if not record:
        return False
    if time.time() > record['expires_at']:
        _store.pop(username, None)
        return False
    record['attempts'] += 1
    if record['attempts'] > 5:
        _store.pop(username, None)
        return False
    if record['otp'] == otp.strip():
        _store.pop(username, None)
        return True
    return False


def _send_email(to_email: str, otp: str, username: str) -> bool:
    sender   = os.environ.get('MAIL_EMAIL', '').strip()
    password = os.environ.get('MAIL_PASSWORD', '').strip()
    if not sender or not password:
        logger.warning('MAIL_EMAIL or MAIL_PASSWORD not set in .env')
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Your OTP: {otp} – Disaster Response System'
        msg['From']    = f'Disaster Response System <{sender}>'
        msg['To']      = to_email

        text = (f'Hello {username},\n\nYour OTP is: {otp}\n'
                f'Valid for 10 minutes. Do not share.\n\n— Disaster Response System')

        html = f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#f4f6f9;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:40px 20px;">
<table width="520" cellpadding="0" cellspacing="0"
       style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.1);">
  <tr><td style="background:#dc3545;padding:28px;text-align:center;">
    <h1 style="color:#fff;margin:0;font-size:22px;">Disaster Response System</h1>
    <p style="color:rgba(255,255,255,.85);margin:6px 0 0;font-size:14px;">Two-Factor Authentication</p>
  </td></tr>
  <tr><td style="padding:36px;text-align:center;">
    <p style="color:#444;font-size:16px;margin:0 0 8px;">Hello <strong>{username}</strong>,</p>
    <p style="color:#666;font-size:14px;margin:0 0 20px;">Your login OTP is:</p>
    <div style="background:#fff5f5;border:2px dashed #dc3545;border-radius:12px;
                padding:22px;margin:0 auto 20px;display:inline-block;min-width:240px;">
      <div style="font-size:52px;font-weight:900;letter-spacing:16px;color:#dc3545;">{otp}</div>
    </div>
    <p style="color:#888;font-size:13px;margin:0;">Valid for <strong>10 minutes</strong>. Do not share.</p>
  </td></tr>
  <tr><td style="background:#f8f9fa;padding:12px;text-align:center;border-top:1px solid #dee2e6;">
    <small style="color:#aaa;font-size:11px;">Autonomous Disaster Response Coordination System</small>
  </td></tr>
</table></td></tr></table>
</body></html>"""

        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15) as server:
            server.login(sender, password)
            server.sendmail(sender, to_email, msg.as_string())
        logger.info('OTP sent to %s', to_email)
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error('Gmail auth failed — check MAIL_EMAIL and MAIL_PASSWORD')
        return False
    except Exception as e:
        logger.error('Email OTP failed: %s', e)
        return False


def generate_and_send_otp(username: str, email: str = '') -> dict:
    """Generate OTP and deliver via Gmail to the user's email address."""
    otp = _make_otp(username)
    if email and _send_email(email, otp, username):
        return {'otp': otp, 'sent': True, 'method': 'email'}
    return {'otp': otp, 'sent': False, 'method': 'fallback'}


def generate_otp(username: str) -> str:
    return _make_otp(username)
