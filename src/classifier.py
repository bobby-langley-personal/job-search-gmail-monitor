"""
Email Classifier

Identifies job-related emails using keyword matching, pattern recognition,
and optional AI classification.
"""

import json
import re
import logging
import os
import urllib.request
from typing import Dict, List

logger = logging.getLogger(__name__)


class EmailClassifier:
    """Classifies emails as job-related with priority levels."""
    
    def __init__(self, config):
        """
        Initialize classifier with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.keywords = config.get('keywords', {})
        self.subject_patterns = config.get('subject_patterns', [])
        self.tracked_domains = config.get('tracked_domains', [])
        self.exclusions = config.get('exclude', {})
        self.ai_enabled = config.get('notifications', {}).get(
            'ai_classification', {}
        ).get('enabled', False)
        
        self.ai_error = None
        if self.ai_enabled:
            try:
                from anthropic import Anthropic
                api_key = os.getenv('ANTHROPIC_API_KEY')
                if api_key:
                    self.ai_client = Anthropic(api_key=api_key)
                    self.ai_model = self._select_model(api_key)
                    if self.ai_model is None:
                        self.ai_enabled = False
                        self.ai_error = (
                            "AI model selection failed: could not retrieve available models "
                            "from the Anthropic API. AI classification is disabled. "
                            "Check your ANTHROPIC_API_KEY and update the code if needed."
                        )
                        logger.error(self.ai_error)
                    else:
                        logger.info(f"AI classification enabled using {self.ai_model}")
                else:
                    logger.warning("AI enabled but ANTHROPIC_API_KEY not set")
                    self.ai_enabled = False
            except ImportError:
                logger.warning("anthropic package not installed, AI disabled")
                self.ai_enabled = False
    
    def classify(self, email: Dict) -> Dict:
        """
        Classify an email as job-related or not.
        
        Args:
            email: Email dictionary with subject, from, body, etc.
            
        Returns:
            Dictionary with classification results:
            {
                'is_job_related': bool,
                'priority': 'high'|'medium'|'low',
                'confidence': float (0-1),
                'reasons': List[str]
            }
        """
        # Check exclusions first
        if self._is_excluded(email):
            return {
                'is_job_related': False,
                'priority': None,
                'confidence': 1.0,
                'reasons': ['Matched exclusion rule']
            }
        
        # Run keyword and pattern matching
        keyword_result = self._keyword_match(email)
        pattern_result = self._pattern_match(email)
        domain_result = self._domain_match(email)
        
        # Combine results
        is_job_related = (
            keyword_result['match'] or 
            pattern_result['match'] or 
            domain_result['match']
        )
        
        priority = max(
            keyword_result.get('priority', 'low'),
            pattern_result.get('priority', 'low'),
            domain_result.get('priority', 'low'),
            key=lambda p: ['low', 'medium', 'high'].index(p)
        )
        
        reasons = []
        reasons.extend(keyword_result.get('reasons', []))
        reasons.extend(pattern_result.get('reasons', []))
        reasons.extend(domain_result.get('reasons', []))
        
        # AI classification if enabled
        if self.ai_enabled and is_job_related:
            ai_result = self._ai_classify(email)
            if ai_result:
                # AI can override if confidence is high
                threshold = self.config.get('notifications', {}).get(
                    'ai_classification', {}
                ).get('confidence_threshold', 0.7)
                
                if ai_result['confidence'] >= threshold:
                    is_job_related = ai_result['is_job_related']
                    priority = ai_result.get('priority', priority)
                    reasons.append(
                        f"AI classification: {ai_result.get('reason', 'N/A')}"
                    )
        
        confidence = self._calculate_confidence(
            keyword_result, pattern_result, domain_result
        )
        
        return {
            'is_job_related': is_job_related,
            'priority': priority if is_job_related else None,
            'confidence': confidence,
            'reasons': reasons
        }
    
    def _is_excluded(self, email: Dict) -> bool:
        """Check if email matches exclusion rules."""
        sender = email.get('from', '').lower()
        subject = email.get('subject', '').lower()
        
        # Check sender exclusions
        excluded_senders = self.exclusions.get('senders', [])
        for excluded in excluded_senders:
            if excluded.lower() in sender:
                logger.debug(f"Excluded sender: {sender}")
                return True
        
        # Check subject exclusions
        excluded_subjects = self.exclusions.get('subjects', [])
        for excluded in excluded_subjects:
            if excluded.lower() in subject:
                logger.debug(f"Excluded subject: {subject}")
                return True
        
        return False
    
    def _keyword_match(self, email: Dict) -> Dict:
        """Match email against keyword lists."""
        text = f"{email.get('subject', '')} {email.get('body', '')}".lower()
        
        # Check high priority keywords
        high_keywords = self.keywords.get('high_priority', [])
        for keyword in high_keywords:
            if keyword.lower() in text:
                return {
                    'match': True,
                    'priority': 'high',
                    'reasons': [f'Matched high priority keyword: "{keyword}"']
                }
        
        # Check medium priority keywords
        medium_keywords = self.keywords.get('medium_priority', [])
        for keyword in medium_keywords:
            if keyword.lower() in text:
                return {
                    'match': True,
                    'priority': 'medium',
                    'reasons': [f'Matched medium priority keyword: "{keyword}"']
                }
        
        # Check low priority keywords
        low_keywords = self.keywords.get('low_priority', [])
        for keyword in low_keywords:
            if keyword.lower() in text:
                return {
                    'match': True,
                    'priority': 'low',
                    'reasons': [f'Matched low priority keyword: "{keyword}"']
                }
        
        return {'match': False, 'priority': 'low', 'reasons': []}
    
    def _pattern_match(self, email: Dict) -> Dict:
        """Match email subject against regex patterns."""
        subject = email.get('subject', '')
        
        for pattern in self.subject_patterns:
            if re.search(pattern, subject, re.IGNORECASE):
                return {
                    'match': True,
                    'priority': 'medium',
                    'reasons': [f'Matched subject pattern: "{pattern}"']
                }
        
        return {'match': False, 'priority': 'low', 'reasons': []}
    
    def _domain_match(self, email: Dict) -> Dict:
        """Check if sender is from a tracked domain."""
        sender = email.get('from', '').lower()
        
        for domain in self.tracked_domains:
            if domain.lower() in sender:
                return {
                    'match': True,
                    'priority': 'medium',
                    'reasons': [f'From tracked domain: {domain}']
                }
        
        return {'match': False, 'priority': 'low', 'reasons': []}
    
    def _select_model(self, api_key: str) -> str | None:
        """Query the models API and return the cheapest available tier (haiku → sonnet → opus).
        Returns None if the models list cannot be fetched."""
        try:
            req = urllib.request.Request(
                'https://api.anthropic.com/v1/models',
                headers={'x-api-key': api_key, 'anthropic-version': '2023-06-01'}
            )
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read())
            model_ids = [m['id'] for m in data.get('data', [])]
            for tier in ('haiku', 'sonnet', 'opus'):
                matches = [m for m in model_ids if tier in m]
                if matches:
                    return matches[0]  # API returns newest first
        except Exception as e:
            logger.error(f"Could not fetch model list: {e}")
        return None

    def _ai_classify(self, email: Dict) -> Dict:
        """Use AI to classify email (if enabled)."""
        try:
            prompt = f"""Analyze this email and determine if it's related to a job search/application.
            
Subject: {email.get('subject', '')}
From: {email.get('from', '')}
Snippet: {email.get('snippet', '')}

Respond with JSON only:
{{
    "is_job_related": true/false,
    "priority": "high/medium/low",
    "confidence": 0.0-1.0,
    "reason": "brief explanation"
}}

High priority: interview invites, offers, urgent next steps
Medium priority: application updates, recruiter outreach
Low priority: general job postings, newsletters"""

            message = self.ai_client.messages.create(
                model=self.ai_model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text.strip()
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('\n', 1)[1]
                response_text = response_text.rsplit('\n', 1)[0]
            
            result = json.loads(response_text)
            return result
            
        except Exception as e:
            logger.error(f"AI classification error: {e}")
            return None
    
    def _calculate_confidence(self, *results) -> float:
        """Calculate overall confidence score."""
        matches = sum(1 for r in results if r.get('match', False))
        if matches == 0:
            return 0.0
        
        # Simple scoring: more matches = higher confidence
        return min(matches / len(results) + 0.3, 1.0)
