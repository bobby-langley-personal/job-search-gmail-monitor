"""
AWS Lambda Handler for Job Search Gmail Monitor

This handler adapts the application to run in AWS Lambda environment.
"""

import json
import logging
import sys
import os
import base64
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gmail_client import GmailClient
from classifier import EmailClassifier
from notifier import Notifier
from state_manager import EmailStateManager
from utils import load_config, setup_logging

# Initialize logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def setup_credentials():
    """Setup Gmail credentials from environment variables."""
    # Use /tmp directory (only writable location in Lambda)
    config_dir = '/tmp/config'
    os.makedirs(config_dir, exist_ok=True)
    
    # Decode and save credentials.json
    creds_b64 = os.environ.get('GMAIL_CREDENTIALS_B64', '')
    if creds_b64:
        credentials_json = base64.b64decode(creds_b64).decode('utf-8')
        with open(f'{config_dir}/credentials.json', 'w') as f:
            f.write(credentials_json)
        logger.info("Credentials file created in /tmp")
    
    # Decode and save token.pickle
    token_b64 = os.environ.get('GMAIL_TOKEN_B64', '')
    if token_b64:
        token_data = base64.b64decode(token_b64)
        with open(f'{config_dir}/token.pickle', 'wb') as f:
            f.write(token_data)
        logger.info("Token file created in /tmp")
    
    # Copy settings.yaml to /tmp as well
    if os.path.exists('config/settings.yaml'):
        import shutil
        shutil.copy('config/settings.yaml', f'{config_dir}/settings.yaml')
        logger.info("Settings copied to /tmp")


def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    
    Args:
        event: Lambda event object (from EventBridge scheduler)
        context: Lambda context object
        
    Returns:
        Response dict with statusCode and body
    """
    try:
        logger.info("Starting Gmail monitor check...")
        
        # Setup credentials from environment
        setup_credentials()
        
        # Load configuration from /tmp
        config_path = '/tmp/config/settings.yaml'
        if not os.path.exists(config_path):
            config_path = 'config/settings.yaml'  # Fallback to packaged version
        
        config = load_config(config_path)
        
        # Initialize components (will look in /tmp/config first)
        gmail_client = GmailClient(credentials_path='/tmp/config/credentials.json')
        classifier = EmailClassifier(config)
        notifier = Notifier(config)
        state_manager = EmailStateManager()
        
        logger.info(f"State: {state_manager.get_stats()}")
        
        # Fetch recent emails
        emails = gmail_client.get_recent_emails(
            max_results=config['gmail']['max_results'],
            labels=config['gmail']['labels_to_check']
        )
        
        logger.info(f"Found {len(emails)} emails to process")
        
        # Classify emails
        job_related_emails = []
        for email in emails:
            classification = classifier.classify(email)
            if classification['is_job_related']:
                job_related_emails.append({
                    'email': email,
                    'priority': classification['priority'],
                    'confidence': classification['confidence'],
                    'reasons': classification['reasons']
                })
        Filter to only new emails (delta detection)
        new_emails = state_manager.get_new_emails(job_related_emails)
        
        if len(new_emails) < len(job_related_emails):
            logger.info(
                f"Filtered to {len(new_emails)} new emails "
                f"({len(job_related_emails) - len(new_emails)} already seen)"
            )
        
        # Send notifications only for new emails
        if new_emails:
            notifier.send_notifications(new_emails)
            logger.info("Notifications sent successfully")
        else:
            logger.info("No new job-related emails found")
        
        # Return success response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Monitor check completed successfully',
                'emails_checked': len(emails),
                'job_related_found': len(job_related_emails),
                'new_emails': len(new
                'message': 'Monitor check completed successfully',
                'emails_checked': len(emails),
                'job_related_found': len(job_related_emails)
            })
        }
        
    except Exception as e:
        logger.error(f"Error in Lambda handler: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
