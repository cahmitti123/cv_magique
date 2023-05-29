import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt



# Pydantic models
class ForgotPasswordRequest(BaseModel):
    email: str

# Forgot Password
@app.post("/forgot-password")
async def forgot_password(user_request: ForgotPasswordRequest, session: AsyncSession = Depends(get_session)):
    # Check if the user exists in the database
    user = await session.execute(select(User).where(User.email == user_request.email))
    user = user.scalar()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate a password reset token
    token = generate_reset_token(user.email)  # Custom function to generate a unique token

    # Send the password reset email with the token
    send_password_reset_email(user.email, token)  # Custom function to send the email

    return {"message": "Password reset email sent"}


# Custom function to generate a unique password reset token
def generate_reset_token(email: str) -> str:
    payload = {
        "sub": email,
        "exp": datetime.utcnow() + timedelta(minutes=int(RESET_TOKEN_EXPIRE_MINUTES)),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


# Custom function to send the password reset email
def send_password_reset_email(email: str, token: str):
    # Email configuration
    sender_email = "your-email@example.com"
    sender_password = "your-email-password"
    smtp_server = "smtp.example.com"
    smtp_port = 587

    # Create a multipart message
    message = MIMEMultipart("alternative")
    message["Subject"] = "Password Reset Request"
    message["From"] = sender_email
    message["To"] = email

    # Create the plain text and HTML versions of the message
    text = f"""
    Hello,

    You have requested to reset your password. Please click the link below to reset your password:

    Reset Password: http://your-website.com/reset-password?token={token}

    If you did not request a password reset, please ignore this email.

    Best regards,
    Your Website Team
    """

    html = f"""
    <html>
    <body>
        <p>Hello,</p>

        <p>You have requested to reset your password. Please click the link below to reset your password:</p>

        <p><a href="http://your-website.com/reset-password?token={token}">Reset Password</a></p>

        <p>If you did not request a password reset, please ignore this email.</p>

        <p>Best regards,<br>Your Website Team</p>
    </body>
    </html>
    """

    # Turn these into plain/text MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    # Attach the plain text and HTML versions to the message
    message.attach(part1)
    message.attach(part2)

    # Connect to the SMTP server and send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, message.as_string())

    print("Password reset email sent")
