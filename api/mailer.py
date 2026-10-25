"""Outgoing messages for password reset.

E-mail goes over HTTPS because Render's free plan blocks the SMTP ports: either a Google Apps Script relay
(MAIL_RELAY_URL + MAIL_RELAY_SECRET, sends from the owner's Gmail) or Brevo's API.
SMS (optional) goes through Twilio. Both return False, and send nothing, when their environment variables are not set.
"""
import base64
import json
import logging
import os
import urllib.parse
import urllib.request

log = logging.getLogger(__name__)
TIMEOUT = 10


def _relay_configured() -> bool:
    return bool(os.getenv("MAIL_RELAY_URL") and os.getenv("MAIL_RELAY_SECRET"))


def email_configured() -> bool:
    return _relay_configured() or bool(os.getenv("BREVO_API_KEY") and os.getenv("MAIL_FROM"))


def sms_configured() -> bool:
    return bool(os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN") and os.getenv("TWILIO_FROM"))


def send_email(to: str, subject: str, text: str) -> bool:
    if not email_configured():
        return False
    if _relay_configured():
        # Apps Script answers a POST with a redirect to its result; urllib re-reads that as a GET, which is what it needs.
        req = urllib.request.Request(
            os.environ["MAIL_RELAY_URL"],
            data=json.dumps({"secret": os.environ["MAIL_RELAY_SECRET"], "to": to, "subject": subject, "text": text}).encode("utf-8"),
            headers={"content-type": "application/json"},
            method="POST",
        )
        try:
            return json.loads(urllib.request.urlopen(req, timeout=TIMEOUT * 2).read()).get("ok") is True
        except Exception as exc:
            log.warning("Password reset e-mail could not be sent: %s", exc)
            return False
    payload = {
        "sender": {"name": os.getenv("MAIL_FROM_NAME", "Nexus ATS"), "email": os.environ["MAIL_FROM"]},
        "to": [{"email": to}],
        "subject": subject,
        "textContent": text,
    }
    req = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=json.dumps(payload).encode("utf-8"),
        headers={"api-key": os.environ["BREVO_API_KEY"], "content-type": "application/json", "accept": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=TIMEOUT).read()
        return True
    except Exception as exc:  # the caller answers the same way whether or not the e-mail went out
        log.warning("Password reset e-mail could not be sent: %s", exc)
        return False


def send_sms(to: str, text: str) -> bool:
    if not sms_configured():
        return False
    sid, token = os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"]
    req = urllib.request.Request(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
        data=urllib.parse.urlencode({"To": to, "From": os.environ["TWILIO_FROM"], "Body": text}).encode("utf-8"),
        headers={"Authorization": "Basic " + base64.b64encode(f"{sid}:{token}".encode()).decode()},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=TIMEOUT).read()
        return True
    except Exception as exc:
        log.warning("Password reset SMS could not be sent: %s", exc)
        return False
