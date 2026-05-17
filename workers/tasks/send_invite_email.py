# Send Invite Email Task - Celery task for sending candidate invitation emails
from celery import shared_task
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import time

# Environment variables for SMTP configuration
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
MAIL_FROM = os.getenv("MAIL_FROM", "noreply@hireiq.com")
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
CANDIDATE_PORTAL_BASE_URL = os.getenv("CANDIDATE_PORTAL_BASE_URL", "http://localhost:5174")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_invite_email(
    self,
    candidate_email: str,
    candidate_name: str,
    job_title: str,
    company_name: str,
    invite_token: str
):
    """
    Send a personalized interview invitation email to a candidate.
    
    Args:
        candidate_email: The candidate's email address
        candidate_name: The candidate's name
        job_title: The job title they're applying for
        company_name: The hiring company's name
        invite_token: The unique invite token for the interview
    
    Retries up to 3 times with a 60-second delay between attempts if the send fails.
    """
    # Construct the interview link
    interview_link = f"{CANDIDATE_PORTAL_BASE_URL}/interview/{invite_token}"
    
    # Create email subject
    subject = f"Interview Invitation: {job_title} at {company_name}"
    
    # Create email body (HTML)
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4A90D9; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 30px 20px; background-color: #f9f9f9; }}
            .button {{ 
                display: inline-block; 
                padding: 12px 30px; 
                background-color: #4A90D9; 
                color: white; 
                text-decoration: none; 
                border-radius: 5px; 
                margin-top: 20px;
            }}
            .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Interview Invitation</h1>
            </div>
            <div class="content">
                <p>Dear {candidate_name or 'Candidate'},</p>
                
                <p>We are pleased to invite you to participate in an AI-powered interview for the position of 
                <strong>{job_title}</strong> at <strong>{company_name}</strong>.</p>
                
                <p>This interview will help us understand your skills and experience better. 
                Please click the button below to begin your interview:</p>
                
                <p style="text-align: center;">
                    <a href="{interview_link}" class="button">Start Interview</a>
                </p>
                
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #4A90D9;">{interview_link}</p>
                
                <p><strong>Important Notes:</strong></p>
                <ul>
                    <li>Please ensure you have a stable internet connection</li>
                    <li>Find a quiet place for your interview</li>
                    <li>The interview link will expire in 7 days</li>
                    <li>You will need camera and microphone access</li>
                </ul>
                
                <p>If you have any questions or concerns, please don't hesitate to contact us.</p>
                
                <p>Best of luck!</p>
                <p>The {company_name} Team</p>
            </div>
            <div class="footer">
                <p>This is an automated message. Please do not reply directly to this email.</p>
                <p>&copy; {company_name}. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Create plain text version
    text_body = f"""
    Dear {candidate_name or 'Candidate'},
    
    We are pleased to invite you to participate in an AI-powered interview for the position of 
    {job_title} at {company_name}.
    
    Please visit the following link to begin your interview:
    {interview_link}
    
    Important Notes:
    - Please ensure you have a stable internet connection
    - Find a quiet place for your interview
    - The interview link will expire in 7 days
    - You will need camera and microphone access
    
    If you have any questions or concerns, please don't hesitate to contact us.
    
    Best of luck!
    The {company_name} Team
    
    ---
    This is an automated message. Please do not reply directly to this email.
    """
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = MAIL_FROM
        msg['To'] = candidate_email
        
        # Attach both plain text and HTML versions
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        # Connect to SMTP server and send email
        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as server:
            server.starttls()  # Enable TLS encryption
            
            # Login if credentials are provided
            if MAIL_USERNAME and MAIL_PASSWORD:
                server.login(MAIL_USERNAME, MAIL_PASSWORD)
            
            # Send email
            server.send_message(msg)
        
        return {
            "success": True,
            "message": f"Email sent successfully to {candidate_email}",
            "email": candidate_email,
            "job_title": job_title
        }
        
    except Exception as e:
        # Retry on failure
        try:
            raise self.retry(exc=e)
        except AttributeError:
            # Not running in Celery context, just return error
            return {
                "success": False,
                "error": str(e),
                "email": candidate_email
            }


# For testing without Celery broker
def send_invite_email_eager(
    candidate_email: str,
    candidate_name: str,
    job_title: str,
    company_name: str,
    invite_token: str
):
    """
    Synchronous version for testing without a Celery broker.
    
    This function attempts an SMTP connection to verify the email functionality works.
    """
    return send_invite_email(
        candidate_email=candidate_email,
        candidate_name=candidate_name,
        job_title=job_title,
        company_name=company_name,
        invite_token=invite_token
    )
