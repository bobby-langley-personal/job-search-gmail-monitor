"""
Utility Functions

Helper functions for configuration, logging, and common operations.
"""

import logging
import yaml
from pathlib import Path
import coloredlogs


def load_config(config_path: str) -> dict:
    """
    Load YAML configuration file.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


def setup_logging(log_level=logging.INFO) -> logging.Logger:
    """
    Set up application logging with colored output.
    
    Args:
        log_level: Logging level (default: INFO)
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # File handler
    file_handler = logging.FileHandler('logs/gmail_monitor.log')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler with colors
    coloredlogs.install(
        level=log_level,
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        logger=logger
    )
    
    return logger


def format_email_preview(email: dict, max_length: int = 100) -> str:
    """
    Format email for display in notifications.
    
    Args:
        email: Email dictionary
        max_length: Maximum length for subject/snippet
        
    Returns:
        Formatted string
    """
    subject = email.get('subject', 'No Subject')[:max_length]
    sender = email.get('from', 'Unknown')[:max_length]
    
    return f"{subject}\nFrom: {sender}"


def get_gmail_url(email_id: str) -> str:
    """
    Generate Gmail web URL for a specific email.
    
    Args:
        email_id: Gmail message ID
        
    Returns:
        Full Gmail URL to view the email (works on web and mobile)
    """
    # Use 'all' instead of 'inbox' for better mobile compatibility
    # and to handle archived/labeled emails
    return f"https://mail.google.com/mail/u/0/#all/{email_id}"
