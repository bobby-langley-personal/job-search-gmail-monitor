"""
Tests for Email Classifier
"""

import pytest
from classifier import EmailClassifier


@pytest.fixture
def config():
    """Sample configuration for testing."""
    return {
        'keywords': {
            'high_priority': ['interview', 'offer'],
            'medium_priority': ['application', 'recruiter'],
            'low_priority': ['career', 'job posting']
        },
        'subject_patterns': [
            r'interview.*',
            r'.*position.*'
        ],
        'tracked_domains': [
            'greenhouse.io',
            'lever.co'
        ],
        'exclude': {
            'senders': ['noreply@linkedin.com'],
            'subjects': ['Daily job alert']
        },
        'notifications': {
            'ai_classification': {
                'enabled': False
            }
        }
    }


@pytest.fixture
def classifier(config):
    """Create classifier instance for testing."""
    return EmailClassifier(config)


def test_high_priority_keyword(classifier):
    """Test high priority keyword detection."""
    email = {
        'subject': 'Interview Request for Software Engineer',
        'from': 'recruiter@company.com',
        'body': 'We would like to schedule an interview...',
        'snippet': 'Interview request'
    }
    
    result = classifier.classify(email)
    
    assert result['is_job_related'] is True
    assert result['priority'] == 'high'


def test_medium_priority_keyword(classifier):
    """Test medium priority keyword detection."""
    email = {
        'subject': 'Application Status Update',
        'from': 'hr@company.com',
        'body': 'Your application has been reviewed...',
        'snippet': 'Application update'
    }
    
    result = classifier.classify(email)
    
    assert result['is_job_related'] is True
    assert result['priority'] == 'medium'


def test_tracked_domain(classifier):
    """Test tracked domain detection."""
    email = {
        'subject': 'New opportunity at TechCo',
        'from': 'jobs@greenhouse.io',
        'body': 'We have a new position...',
        'snippet': 'New position'
    }
    
    result = classifier.classify(email)
    
    assert result['is_job_related'] is True


def test_exclusion_rule(classifier):
    """Test exclusion rules."""
    email = {
        'subject': 'Daily job alert',
        'from': 'noreply@linkedin.com',
        'body': 'Here are today\'s job recommendations...',
        'snippet': 'Job recommendations'
    }
    
    result = classifier.classify(email)
    
    assert result['is_job_related'] is False


def test_subject_pattern(classifier):
    """Test subject pattern matching."""
    email = {
        'subject': 'Software Engineer Position Available',
        'from': 'hr@startup.com',
        'body': 'We are hiring...',
        'snippet': 'Hiring'
    }
    
    result = classifier.classify(email)
    
    assert result['is_job_related'] is True


def test_non_job_email(classifier):
    """Test that non-job emails are filtered out."""
    email = {
        'subject': 'Meeting reminder',
        'from': 'calendar@google.com',
        'body': 'Don\'t forget your meeting tomorrow...',
        'snippet': 'Meeting reminder'
    }
    
    result = classifier.classify(email)
    
    assert result['is_job_related'] is False
