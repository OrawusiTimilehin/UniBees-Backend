import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

async def send_otp_email(target_email: str, otp_code: str):
    """
    Sends a real branded verification email via SMTP.
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM", "UniBees <noreply@unibees.com>")

    if not smtp_user or not smtp_pass:
        print("ERROR: Email credentials missing in .env")
        return False

    # Create the email container
    message = MIMEMultipart("alternative")
    message["Subject"] = f"🐝 {otp_code} is your UniBees verification code"
    message["From"] = smtp_from
    message["To"] = target_email

    # Professional Branded HTML Template
    html = f"""
    <html>
      <body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 500px; margin: auto; background: #ffffff; padding: 40px; border-radius: 30px; border: 1px solid #e0e0e0; text-align: center;">
          <div style="font-size: 50px; margin-bottom: 20px;">🐝</div>
          <h2 style="color: #1a1a1a; margin-top: 0;">Verify your wing</h2>
          <p style="color: #666666; font-size: 16px; line-height: 1.5;">
            Welcome to the Hive! Use the verification code below to confirm your university email address.
          </p>
          <div style="background: #FFFBEB; border: 2px dashed #FFC845; padding: 20px; border-radius: 15px; font-size: 36px; font-weight: 900; color: #000; letter-spacing: 12px; margin: 30px 0;">
            {otp_code}
          </div>
          <p style="font-size: 13px; color: #999999;">
            This code will expire in 10 minutes. If you didn't request this, you can safely ignore this email.
          </p>
          <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
          <p style="font-size: 11px; color: #ccc; text-transform: uppercase; letter-spacing: 1px;">
            UniBees • Stigmergic Campus Discovery
          </p>
        </div>
      </body>
    </html>
    """
    
    message.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls() # Secure the connection
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, target_email, message.as_string())
        print(f"SUCCESS: OTP sent to {target_email}")
        return True
    except Exception as e:
        print(f"FAILED TO SEND EMAIL: {e}")
        return False