#!/usr/bin/env python3
"""
Job Search Gmail Monitor - Main Entry Point

Monitors Gmail for job-related emails and sends notifications.
"""

import argparse
import logging
import time
import sys
from pathlib import Path

from dotenv import load_dotenv
import coloredlogs

from gmail_client import GmailClient
from classifier import EmailClassifier
from notifier import Notifier
from utils import load_config, setup_logging


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor Gmail for job search related emails"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run continuously in background"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Check interval in seconds (default: 300)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/settings.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logging(log_level)
    
    # Load configuration
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        logger.error(
            f"Configuration file not found: {args.config}\n"
            "Please copy config/settings.example.yaml to config/settings.yaml"
        )
        sys.exit(1)
    
    logger.info("Starting Job Search Gmail Monitor")
    logger.info(f"Configuration loaded from: {args.config}")
    
    # Initialize components
    try:
        gmail_client = GmailClient()
        classifier = EmailClassifier(config)
        notifier = Notifier(config)
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        sys.exit(1)
    
    def check_emails():
        """Check for new job-related emails and send notifications."""
        try:
            logger.info("Checking for new emails...")
            
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
                        'confidence': classification['confidence']
                    })
            
            logger.info(
                f"Identified {len(job_related_emails)} job-related emails"
            )
            
            # Send notifications
            if job_related_emails:
                notifier.send_notifications(job_related_emails)
                logger.info("Notifications sent successfully")
            else:
                logger.info("No job-related emails found")
                
        except Exception as e:
            logger.error(f"Error during email check: {e}", exc_info=True)
    
    # Run once or continuously
    if args.daemon:
        logger.info(
            f"Running in daemon mode (checking every {args.interval} seconds)"
        )
        logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                check_emails()
                logger.debug(f"Sleeping for {args.interval} seconds...")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            logger.info("Shutting down gracefully...")
    else:
        check_emails()
        logger.info("Single check complete")


if __name__ == "__main__":
    main()
