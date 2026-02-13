"""
Notifier

Handles sending notifications via email and SMS.
"""

import os
import logging
from typing import List, Dict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from datetime import datetime
from utils import get_gmail_url

logger = logging.getLogger(__name__)


class Notifier:
    """Handles email and SMS notifications."""
    
    def __init__(self, config):
        """
        Initialize notifier with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.email_enabled = config.get('notifications', {}).get(
            'email', {}
        ).get('enabled', False)
        self.sms_enabled = config.get('notifications', {}).get(
            'sms', {}
        ).get('enabled', False)
        self.sms_high_priority_only = config.get('notifications', {}).get(
            'sms', {}
        ).get('only_high_priority', True)
        
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.notification_email = os.getenv('NOTIFICATION_EMAIL')
        
        # SMS configuration
        if self.sms_enabled:
            try:
                from twilio.rest import Client
                account_sid = os.getenv('TWILIO_ACCOUNT_SID')
                auth_token = os.getenv('TWILIO_AUTH_TOKEN')
                
                if account_sid and auth_token:
                    self.twilio_client = Client(account_sid, auth_token)
                    self.twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
                    self.your_phone = os.getenv('YOUR_PHONE_NUMBER')
                    logger.info("SMS notifications enabled")
                else:
                    logger.warning("SMS enabled but Twilio credentials missing")
                    self.sms_enabled = False
            except ImportError:
                logger.warning("twilio package not installed, SMS disabled")
                self.sms_enabled = False
    
    def send_notifications(self, job_emails: List[Dict]):
        """
        Send notifications for job-related emails.
        
        Args:
            job_emails: List of classified email dictionaries
        """
        if not job_emails:
            return
        
        # Sort by priority
        high_priority = [e for e in job_emails if e['priority'] == 'high']
        medium_priority = [e for e in job_emails if e['priority'] == 'medium']
        low_priority = [e for e in job_emails if e['priority'] == 'low']
        
        # Send email notification
        if self.email_enabled:
            self._send_email_digest(high_priority, medium_priority, low_priority)
        
        # Send SMS for high priority only
        if self.sms_enabled and high_priority:
            if not self.sms_high_priority_only or high_priority:
                self._send_sms_alert(high_priority)
    
    def _send_email_digest(
        self, 
        high_priority: List[Dict],
        medium_priority: List[Dict],
        low_priority: List[Dict]
    ):
        """Send email digest of job-related emails."""
        try:
            subject = self.config.get('notifications', {}).get(
                'email', {}
            ).get('subject', 'Job Search Update')
            
            # Build HTML email
            html_content = self._build_email_html(
                high_priority, medium_priority, low_priority
            )
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_username
            msg['To'] = self.notification_email
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email digest sent to {self.notification_email}")
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
    
    def _build_email_html(
        self,
        high_priority: List[Dict],
        medium_priority: List[Dict],
        low_priority: List[Dict]
    ) -> str:
        """Build HTML content for email digest."""
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; }}
                .priority-section {{ margin: 20px 0; }}
                .high {{ border-left: 4px solid #f44336; padding-left: 10px; }}
                .medium {{ border-left: 4px solid #ff9800; padding-left: 10px; }}
                .low {{ border-left: 4px solid #2196F3; padding-left: 10px; }}
                .email-item {{ background-color: #f5f5f5; padding: 10px; margin: 10px 0; }}
                .subject {{ font-weight: bold; }}
                .from {{ color: #666; font-size: 0.9em; }}
                .footer {{ margin-top: 30px; color: #999; font-size: 0.8em; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Job Search Update</h1>
                </div>
        """
        
        if high_priority:
            html += """
                <div class="priority-section high">
                    <h2>🔴 High Priority</h2>
            """
            for item in high_priority:
                email = item['email']
                gmail_url = get_gmail_url(email['id'])
                triggers = '<br>'.join(f"• {r}" for r in item.get('reasons', []))
                # Show message ID for mobile users who can manually search
                msg_preview = email['id'][:16] + '...' if len(email['id']) > 16 else email['id']
                html += f"""
                    <div class="email-item">
                        <div class="subject"><a href="{gmail_url}" style="color: #1a73e8; text-decoration: none;">{email['subject']}</a></div>
                        <div class="from">From: {email['from']}</div>
                        <div class="snippet">{email['snippet'][:150]}...</div>
                        <div style="font-size: 0.85em; color: #666; margin-top: 5px;">
                            <strong>Triggers:</strong><br>{triggers}
                        </div>
                        <a href="{gmail_url}" style="display: inline-block; margin-top: 10px; padding: 8px 16px; background-color: #1a73e8; color: white; text-decoration: none; border-radius: 4px;">View in Gmail</a>
                        <div style="font-size: 0.75em; color: #999; margin-top: 5px;">Mobile: Search Gmail for subject "{email['subject'][:30]}..."</div>
                    </div>
                """
            html += "</div>"
        
        if medium_priority:
            html += """
                <div class="priority-section medium">
                    <h2>🟠 Medium Priority</h2>
            """
            for item in medium_priority:
                email = item['email']
                gmail_url = get_gmail_url(email['id'])
                triggers = '<br>'.join(f"• {r}" for r in item.get('reasons', []))
                html += f"""
                    <div class="email-item">
                        <div class="subject"><a href="{gmail_url}" style="color: #1a73e8; text-decoration: none;">{email['subject']}</a></div>
                        <div class="from">From: {email['from']}</div>
                        <div style="font-size: 0.85em; color: #666; margin-top: 5px;">
                            <strong>Triggers:</strong><br>{triggers}
                        </div>
                        <a href="{gmail_url}" style="display: inline-block; margin-top: 10px; padding: 8px 16px; background-color: #1a73e8; color: white; text-decoration: none; border-radius: 4px;">View in Gmail</a>
                        <div style="font-size: 0.75em; color: #999; margin-top: 5px;">Mobile: Search Gmail for subject "{email['subject'][:30]}..."</div>
                    </div>
                """
            html += "</div>"
        
        if low_priority:
            html += """
                <div class="priority-section low">
                    <h2>🔵 Low Priority</h2>
            """
            for item in low_priority:
                email = item['email']
                gmail_url = get_gmail_url(email['id'])
                triggers = '<br>'.join(f"• {r}" for r in item.get('reasons', []))
                html += f"""
                    <div class="email-item">
                        <div class="subject"><a href="{gmail_url}" style="color: #1a73e8; text-decoration: none;">{email['subject']}</a></div>
                        <div class="from">From: {email['from']}</div>
                        <div style="font-size: 0.85em; color: #666; margin-top: 5px;">
                            <strong>Triggers:</strong><br>{triggers}
                        </div>
                        <a href="{gmail_url}" style="display: inline-block; margin-top: 10px; padding: 8px 16px; background-color: #1a73e8; color: white; text-decoration: none; border-radius: 4px;">View in Gmail</a>
                        <div style="font-size: 0.75em; color: #999; margin-top: 5px;">Mobile: Search Gmail for subject "{email['subject'][:30]}..."</div>
                    </div>
                """
            html += "</div>"
        
        total = len(high_priority) + len(medium_priority) + len(low_priority)
        html += f"""
                <div class="footer">
                    <p>Total: {total} job-related emails found</p>
                    <p>Generated by Job Search Gmail Monitor</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _send_sms_alert(self, high_priority: List[Dict]):
        """Send SMS alert for high priority emails."""
        try:
            count = len(high_priority)
            
            if count == 1:
                email = high_priority[0]['email']
                message = (
                    f"🔴 Job Alert!\n\n"
                    f"{email['subject'][:100]}\n\n"
                    f"From: {email['from'][:50]}"
                )
            else:
                subjects = [e['email']['subject'][:40] for e in high_priority[:3]]
                message = (
                    f"🔴 {count} Job Alerts!\n\n"
                    + "\n".join(f"• {s}" for s in subjects)
                )
                if count > 3:
                    message += f"\n\n...and {count - 3} more"
            
            # Send SMS via Twilio
            self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone,
                to=self.your_phone
            )
            
            logger.info(f"SMS alert sent for {count} high priority emails")
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
