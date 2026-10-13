"""
Email utility for sending password reset verification codes.
Configured to deliver password reset codes exclusively to the target email:
utkarshbelsare9@gmail.com (configurable via FORGOT_PASSWORD_TARGET_EMAIL).
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import current_app


def send_password_reset_code(user, code, target_email=None):
    """
    Sends a 6-digit password reset verification code to target_email.
    If target_email is None, defaults to current_app.config["FORGOT_PASSWORD_TARGET_EMAIL"]
    (which is utkarshbelsare9@gmail.com).

    Returns:
        (bool, str): (success, detail_message)
    """
    config = current_app.config
    recipient = target_email or config.get("FORGOT_PASSWORD_TARGET_EMAIL", "utkarshbelsare9@gmail.com")

    smtp_server = config.get("MAIL_SERVER", "smtp.gmail.com")
    smtp_port = config.get("MAIL_PORT", 587)
    use_tls = config.get("MAIL_USE_TLS", True)
    username = str(config.get("MAIL_USERNAME", "")).strip()
    password = str(config.get("MAIL_PASSWORD", "")).replace(" ", "").strip()
    sender = config.get("MAIL_DEFAULT_SENDER") or f"ProductivityAI Security <{username}>"

    subject = f"Password Reset Code: {code} - ProductivityAI"
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    text_body = f"""Hello,

A password reset request was initiated for an account on ProductivityAI:
- Requested Username: {user.username}
- Account Email: {user.email}
- Timestamp: {timestamp}

Your 6-Digit Verification Code is:
==================================
           {code}
==================================

This code is valid for 15 minutes.
Recipient designated: {recipient}

If you did not request this password reset, you can safely ignore this email.

Best regards,
ProductivityAI Security Team
"""

    html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: #f1f5f9;
      margin: 0;
      padding: 30px 15px;
      color: #1e293b;
    }}
    .email-container {{
      max-width: 520px;
      margin: 0 auto;
      background: #ffffff;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
      border: 1px solid #e2e8f0;
    }}
    .email-header {{
      background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
      padding: 30px 24px;
      text-align: center;
      color: #ffffff;
    }}
    .email-header h1 {{
      margin: 0;
      font-size: 22px;
      font-weight: 700;
      letter-spacing: -0.5px;
    }}
    .email-header p {{
      margin: 6px 0 0 0;
      font-size: 13px;
      opacity: 0.9;
    }}
    .email-body {{
      padding: 32px 28px;
    }}
    .greeting {{
      font-size: 16px;
      font-weight: 600;
      margin-bottom: 12px;
      color: #0f172a;
    }}
    .instruction {{
      font-size: 14px;
      line-height: 1.6;
      color: #475569;
      margin-bottom: 24px;
    }}
    .code-box {{
      background: #f8fafc;
      border: 2px dashed #6366f1;
      border-radius: 12px;
      text-align: center;
      padding: 22px 16px;
      margin: 20px 0 28px 0;
    }}
    .code-digits {{
      font-size: 38px;
      font-weight: 800;
      letter-spacing: 8px;
      color: #4338ca;
      font-family: 'Courier New', Courier, monospace;
    }}
    .code-caption {{
      font-size: 12px;
      color: #64748b;
      margin-top: 8px;
      font-weight: 500;
    }}
    .details-card {{
      background: #f8fafc;
      border-radius: 10px;
      padding: 14px 18px;
      font-size: 13px;
      color: #334155;
      margin-bottom: 24px;
      border: 1px solid #e2e8f0;
    }}
    .details-card table {{
      width: 100%;
      border-collapse: collapse;
    }}
    .details-card td {{
      padding: 4px 0;
    }}
    .details-card td.label {{
      color: #64748b;
      width: 140px;
    }}
    .details-card td.val {{
      font-weight: 600;
      color: #1e293b;
    }}
    .email-footer {{
      background: #f8fafc;
      padding: 18px 24px;
      text-align: center;
      font-size: 12px;
      color: #94a3b8;
      border-top: 1px solid #e2e8f0;
    }}
  </style>
</head>
<body>
  <div class="email-container">
    <div class="email-header">
      <h1>ProductivityAI Security</h1>
      <p>Password Reset Verification</p>
    </div>
    <div class="email-body">
      <div class="greeting">Hello,</div>
      <div class="instruction">
        A request was submitted to reset the password for your ProductivityAI account.
        Please enter the verification code below to proceed with resetting your password:
      </div>

      <div class="code-box">
        <div class="code-digits">{code}</div>
        <div class="code-caption">⏳ Valid for 15 minutes &middot; Do not share with anyone</div>
      </div>

      <div class="details-card">
        <table>
          <tr>
            <td class="label">Target Account:</td>
            <td class="val">{user.username}</td>
          </tr>
          <tr>
            <td class="label">Registered Email:</td>
            <td class="val">{user.email}</td>
          </tr>
          <tr>
            <td class="label">Sent To:</td>
            <td class="val">{recipient}</td>
          </tr>
          <tr>
            <td class="label">Requested At:</td>
            <td class="val">{timestamp}</td>
          </tr>
        </table>
      </div>

      <div style="font-size: 12px; color: #94a3b8; line-height: 1.5;">
        If you did not request this password reset, no action is needed. Your current password remains secure.
      </div>
    </div>
    <div class="email-footer">
      &copy; ProductivityAI &middot; All rights reserved.
    </div>
  </div>
</body>
</html>"""

    # Assemble MIME message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # If SMTP credentials are provided, send live email
    if username and password:
        try:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=12) as server:
                if use_tls:
                    server.starttls()
                server.login(username, password)
                server.sendmail(sender, [recipient], msg.as_string())
            print(f"[MAILER] Password reset code successfully sent to {recipient} via SMTP!")
            return True, f"Code sent successfully to {recipient}"
        except Exception as e:
            err_msg = f"SMTP connection error while sending to {recipient}: {e}"
            print(f"[MAILER ERROR] {err_msg}")
            return False, err_msg
    else:
        # SMTP credentials not configured in .env yet
        print(f"[MAILER NOTICE] Password reset code '{code}' generated for account '{user.username}'.")
        print(f"[MAILER NOTICE] Target recipient: {recipient}")
        print(f"[MAILER NOTICE] Note: To deliver live email over Google SMTP, add MAIL_USERNAME and MAIL_PASSWORD in .env")
        return False, "SMTP credentials (MAIL_USERNAME/MAIL_PASSWORD) not configured in .env."
