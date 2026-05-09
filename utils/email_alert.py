"""
utils/email_alert.py
--------------------
Sends Gmail email alerts when a blood request is marked Urgent or Emergency
and a matching donor is found.

Reads GMAIL_SENDER and GMAIL_PASSWORD from the .env file in the project root.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load .env from the project root (one level above utils/)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_ROOT, ".env"))

GMAIL_SENDER   = os.getenv("GMAIL_SENDER", "")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD", "")   # App Password recommended


# ── HTML email template ───────────────────────────────────────────────────────

def _build_html(
    requestor_name: str,
    requestor_email: str,
    blood_group: str,
    hospital: str,
    quantity_ml: int,
    urgency: str,
    donor_name: str,
    donor_phone: str,
    donor_email: str,
    donor_location: str,
    donor_date: str,
    donor_time: str,
) -> str:
    urgency_color = "#C0392B" if "Emergency" in urgency else "#E67E22"
    urgency_icon  = "🚨" if "Emergency" in urgency else "⚠️"

    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <style>
    body      {{ font-family: Arial, sans-serif; background: #f4f4f4; margin:0; padding:0; }}
    .wrapper  {{ max-width: 600px; margin: 30px auto; background: #fff;
                border-radius: 10px; overflow: hidden;
                box-shadow: 0 4px 20px rgba(0,0,0,0.12); }}
    .header   {{ background: {urgency_color}; color: #fff; padding: 28px 32px; }}
    .header h1{{ margin:0; font-size:1.5rem; }}
    .header p {{ margin:6px 0 0; font-size:0.9rem; opacity:.85; }}
    .body     {{ padding: 28px 32px; color: #333; }}
    .badge    {{ display:inline-block; background:{urgency_color}; color:#fff;
                padding:4px 14px; border-radius:20px; font-size:0.85rem;
                font-weight:700; margin-bottom:18px; }}
    table     {{ width:100%; border-collapse:collapse; margin-top:12px; }}
    th        {{ background:#fdf3f3; color:{urgency_color}; text-align:left;
                padding:10px 14px; font-size:0.8rem; text-transform:uppercase;
                letter-spacing:.5px; border-bottom:2px solid #f0d0d0; }}
    td        {{ padding:11px 14px; border-bottom:1px solid #f0e0e0;
                font-size:0.92rem; color:#444; }}
    tr:last-child td{{ border-bottom:none; }}
    .section-label{{ font-size:0.78rem; font-weight:700; color:#999;
                     text-transform:uppercase; letter-spacing:.6px;
                     margin:22px 0 6px; }}
    .footer   {{ background:#fdf3f3; padding:18px 32px; font-size:0.78rem;
                color:#999; text-align:center; }}
    .cta      {{ display:block; margin:20px auto 0; width:fit-content;
                background:{urgency_color}; color:#fff; padding:12px 28px;
                border-radius:8px; text-decoration:none; font-weight:700; }}
  </style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>{urgency_icon} Blood Alert — LifeLine Blood Bank</h1>
    <p>A matching donor has been found for your {blood_group} blood request.</p>
  </div>
  <div class="body">
    <div class="badge">{urgency}</div>

    <p>Dear <strong>{requestor_name}</strong>,</p>
    <p>
      We have matched a <strong>{blood_group}</strong> donor to your urgent request.
      Please review the donor details below and coordinate with your hospital
      team immediately.
    </p>

    <div class="section-label">🏥 Request Summary</div>
    <table>
      <tr><th>Field</th><th>Details</th></tr>
      <tr><td>Blood Group</td><td><strong>{blood_group}</strong></td></tr>
      <tr><td>Hospital / Centre</td><td>{hospital}</td></tr>
      <tr><td>Quantity Required</td><td>{quantity_ml} ml</td></tr>
      <tr><td>Urgency Level</td><td>{urgency}</td></tr>
    </table>

    <div class="section-label">💉 Matched Donor Details</div>
    <table>
      <tr><th>Field</th><th>Details</th></tr>
      <tr><td>Donor Name</td><td><strong>{donor_name}</strong></td></tr>
      <tr><td>Donor Phone</td><td>{donor_phone}</td></tr>
      <tr><td>Donor Email</td><td>{donor_email}</td></tr>
      <tr><td>Donation Location</td><td>{donor_location}</td></tr>
      <tr><td>Scheduled Date</td><td>{donor_date}</td></tr>
      <tr><td>Time Slot</td><td>{donor_time}</td></tr>
    </table>

    <p style="margin-top:22px; font-size:0.88rem; color:#555;">
      Please contact the donor directly or call our emergency helpline at
      <strong>+91 98450-00001</strong> for immediate assistance.
    </p>
  </div>
  <div class="footer">
    This is an automated alert from LifeLine Blood Bank. Do not reply to this email.<br/>
    © LifeLine Blood Bank, Bengaluru
  </div>
</div>
</body>
</html>
"""


# ── Plain-text fallback ───────────────────────────────────────────────────────

def _build_plain(
    requestor_name, blood_group, hospital, quantity_ml, urgency,
    donor_name, donor_phone, donor_email, donor_location, donor_date, donor_time,
) -> str:
    return f"""
LifeLine Blood Bank — {urgency} Alert
{'=' * 50}

Dear {requestor_name},

A matching {blood_group} donor has been found for your request.

REQUEST SUMMARY
  Blood Group   : {blood_group}
  Hospital      : {hospital}
  Quantity      : {quantity_ml} ml
  Urgency       : {urgency}

MATCHED DONOR DETAILS
  Name          : {donor_name}
  Phone         : {donor_phone}
  Email         : {donor_email}
  Location      : {donor_location}
  Date          : {donor_date}
  Time Slot     : {donor_time}

Please contact the donor directly or call +91 98450-00001 for help.

— LifeLine Blood Bank, Bengaluru
"""


# ── Public API ────────────────────────────────────────────────────────────────

def send_blood_alert_email(
    *,
    requestor_name: str,
    requestor_email: str,
    blood_group: str,
    hospital: str,
    quantity_ml: int,
    urgency: str,
    donor_name: str,
    donor_phone: str,
    donor_email: str,
    donor_location: str,
    donor_date: str,
    donor_time: str,
) -> tuple[bool, str]:
    """
    Send an HTML email alert to the requestor.

    Returns
    -------
    (success: bool, message: str)
        success=True  → email sent without error
        success=False → error description returned in message
    """
    if not GMAIL_SENDER or not GMAIL_PASSWORD:
        return False, (
            "GMAIL_SENDER or GMAIL_PASSWORD not set in .env. "
            "Email alert skipped."
        )

    subject = (
        f"🚨 EMERGENCY Blood Alert — {blood_group} Donor Found | LifeLine"
        if "Emergency" in urgency
        else f"⚠️ Urgent Blood Alert — {blood_group} Donor Found | LifeLine"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"LifeLine Blood Bank <{GMAIL_SENDER}>"
    msg["To"]      = requestor_email

    plain = _build_plain(
        requestor_name, blood_group, hospital, quantity_ml, urgency,
        donor_name, donor_phone, donor_email, donor_location, donor_date, donor_time,
    )
    html = _build_html(
        requestor_name, requestor_email, blood_group, hospital, quantity_ml, urgency,
        donor_name, donor_phone, donor_email, donor_location, donor_date, donor_time,
    )

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html,  "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_SENDER, requestor_email, msg.as_string())
        return True, f"Email alert sent to {requestor_email}"
    except smtplib.SMTPAuthenticationError:
        return False, (
            "Gmail authentication failed. "
            "Make sure you are using an App Password (not your account password) "
            "and that 2-Step Verification is enabled on the sender account."
        )
    except Exception as exc:
        return False, f"Failed to send email: {exc}"