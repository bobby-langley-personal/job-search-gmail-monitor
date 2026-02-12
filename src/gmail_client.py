"""
Gmail API Client

Handles authentication and email retrieval from Gmail.
"""

import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import logging

logger = logging.getLogger(__name__)

# Gmail API scopes - read-only access
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailClient:
    """Wrapper for Gmail API operations."""
    
    def __init__(self, credentials_path='config/credentials.json'):
        """
        Initialize Gmail client with OAuth credentials.
        
        Args:
            credentials_path: Path to OAuth credentials JSON file
        """
        self.credentials_path = credentials_path
        # Use /tmp for token in Lambda, local path otherwise
        if credentials_path.startswith('/tmp'):
            self.token_path = '/tmp/config/token.pickle'
        else:
            self.token_path = 'config/token.pickle'
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail API using OAuth."""
        creds = None
        
        # Load saved credentials if available
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If credentials are invalid or don't exist, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials...")
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_path}\n"
                        "Please download OAuth credentials from Google Cloud Console"
                    )
                
                logger.info("Starting OAuth flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for future use
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
            logger.info("Credentials saved")
        
        # Build Gmail service
        self.service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail API client initialized")
    
    def get_recent_emails(self, max_results=50, labels=None, days_back=7):
        """
        Fetch recent emails from Gmail.
        
        Args:
            max_results: Maximum number of emails to retrieve
            labels: List of label IDs to filter by (e.g., ['INBOX'])
            days_back: How many days back to search
            
        Returns:
            List of email dictionaries with metadata
        """
        if labels is None:
            labels = ['INBOX']
        
        # Calculate date filter
        after_date = datetime.now() - timedelta(days=days_back)
        after_timestamp = int(after_date.timestamp())
        
        # Build query
        query_parts = [f'after:{after_timestamp}']
        label_query = ' OR '.join([f'label:{label}' for label in labels])
        query = f'{" ".join(query_parts)} ({label_query})'
        
        logger.debug(f"Gmail query: {query}")
        
        try:
            # Get message list
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                logger.info("No messages found")
                return []
            
            # Fetch full message details
            emails = []
            for msg in messages:
                email_data = self._get_message_details(msg['id'])
                if email_data:
                    emails.append(email_data)
            
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            raise
    
    def _get_message_details(self, msg_id):
        """
        Get detailed information for a specific message.
        
        Args:
            msg_id: Gmail message ID
            
        Returns:
            Dictionary with email details
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()
            
            headers = message['payload'].get('headers', [])
            header_dict = {h['name'].lower(): h['value'] for h in headers}
            
            # Extract body
            body = self._extract_body(message['payload'])
            
            return {
                'id': msg_id,
                'thread_id': message['threadId'],
                'subject': header_dict.get('subject', ''),
                'from': header_dict.get('from', ''),
                'to': header_dict.get('to', ''),
                'date': header_dict.get('date', ''),
                'body': body,
                'snippet': message.get('snippet', ''),
                'labels': message.get('labelIds', [])
            }
            
        except Exception as e:
            logger.error(f"Error fetching message {msg_id}: {e}")
            return None
    
    def _extract_body(self, payload):
        """Extract email body from message payload."""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        import base64
                        body = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8')
                        break
        elif 'body' in payload and 'data' in payload['body']:
            import base64
            body = base64.urlsafe_b64decode(
                payload['body']['data']
            ).decode('utf-8')
        
        return body
