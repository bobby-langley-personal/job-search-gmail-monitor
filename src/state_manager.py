"""
Email State Manager

Tracks which emails have been processed to avoid duplicate notifications.
Stores state in a JSON file (local development) or /tmp (Lambda).
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Set, Dict, List
import logging

logger = logging.getLogger(__name__)


class EmailStateManager:
    """Manages state of processed emails to detect deltas."""
    
    def __init__(self, state_file='email_state.json'):
        """
        Initialize state manager.
        
        Args:
            state_file: Name of the state file (will be in logs/ locally or /tmp in Lambda)
        """
        # Use /tmp in Lambda, logs/ directory locally
        if os.path.exists('/var/task'):  # Lambda environment
            self.state_dir = Path('/tmp')
        else:
            self.state_dir = Path('logs')
            self.state_dir.mkdir(exist_ok=True)
        
        self.state_file = self.state_dir / state_file
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                logger.info(f"Loaded state with {len(state.get('seen_emails', []))} seen emails")
                return state
            except Exception as e:
                logger.warning(f"Failed to load state: {e}, starting fresh")
        
        return {
            'seen_emails': [],
            'last_run': None
        }
    
    def _save_state(self):
        """Save state to file."""
        try:
            self.state['last_run'] = datetime.now().isoformat()
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            logger.debug(f"State saved to {self.state_file}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def get_new_emails(self, all_job_emails: List[Dict]) -> List[Dict]:
        """
        Filter emails to only those not seen before.
        
        Args:
            all_job_emails: List of job-related email dicts with 'email' key
            
        Returns:
            List of new job-related emails (not seen in previous runs)
        """
        seen_ids = set(self.state.get('seen_emails', []))
        new_emails = []
        
        for job_email in all_job_emails:
            email_id = job_email['email']['id']
            if email_id not in seen_ids:
                new_emails.append(job_email)
                seen_ids.add(email_id)
        
        logger.info(f"Found {len(new_emails)} new emails out of {len(all_job_emails)} total")
        
        # Update state with newly seen emails
        self.state['seen_emails'] = list(seen_ids)
        
        # Prune old email IDs (keep last 7 days worth)
        self._prune_old_emails()
        
        # Save updated state
        self._save_state()
        
        return new_emails
    
    def _prune_old_emails(self, days_to_keep=7):
        """
        Remove old email IDs from state to prevent unbounded growth.
        
        Note: This is a simple implementation. In production, you'd want
        to track timestamps per email ID for more accurate pruning.
        """
        seen_emails = self.state.get('seen_emails', [])
        
        # Simple pruning: keep only last 1000 IDs
        # This prevents memory issues while keeping enough history
        max_ids = 1000
        if len(seen_emails) > max_ids:
            self.state['seen_emails'] = seen_emails[-max_ids:]
            logger.info(f"Pruned state to {max_ids} most recent email IDs")
    
    def reset_state(self):
        """Reset state (useful for testing)."""
        self.state = {
            'seen_emails': [],
            'last_run': None
        }
        self._save_state()
        logger.info("State reset")
    
    def get_stats(self) -> Dict:
        """Get statistics about tracked state."""
        return {
            'total_seen': len(self.state.get('seen_emails', [])),
            'last_run': self.state.get('last_run'),
            'state_file': str(self.state_file)
        }
