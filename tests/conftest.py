"""
Pytest configuration and fixtures for testing
Provides reusable test fixtures and configuration
"""

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    print("pytest not installed. Install with: pip install pytest")

import os
import tempfile
from datetime import datetime, timedelta
from flask import Flask
from flask_login import login_user

# Set testing environment
os.environ['FLASK_ENV'] = 'testing'
os.environ['TESTING'] = 'True'


@pytest.fixture(scope='session')
def app():
    """
    Create and configure a Flask application for testing
    
    Yields:
        Flask app instance
    """
    from app_pro import create_app
    from extensions import db
    
    # Create a temporary database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    # Configure app for testing
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'REDIS_URL': 'redis://localhost:6379/15',  # Use different Redis DB for testing
        'CACHE_TYPE': 'SimpleCache',  # Use simple cache for testing
        'RATELIMIT_ENABLED': False,  # Disable rate limiting in tests
        'MAIL_SUPPRESS_SEND': True,  # Don't send emails in tests
        'SERVER_NAME': 'localhost.localdomain'
    }
    
    app = create_app(test_config)
    
    # Create application context
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope='function')
def client(app):
    """
    Create a test client for the app
    
    Args:
        app: Flask app fixture
        
    Returns:
        Flask test client
    """
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """
    Create a CLI test runner for the app
    
    Args:
        app: Flask app fixture
        
    Returns:
        CLI test runner
    """
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def db_session(app):
    """
    Create a database session for testing
    
    Args:
        app: Flask app fixture
        
    Yields:
        SQLAlchemy session
    """
    from extensions import db
    
    with app.app_context():
        # Begin a nested transaction
        connection = db.engine.connect()
        transaction = connection.begin()
        
        # Bind session to connection
        session = db.create_scoped_session(
            options={'bind': connection, 'binds': {}}
        )
        db.session = session
        
        yield session
        
        # Rollback transaction
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope='function')
def sample_user(db_session):
    """
    Create a sample user for testing
    
    Args:
        db_session: Database session fixture
        
    Returns:
        User instance
    """
    from models import User
    
    user = User(
        email='test@pittstate.edu',
        first_name='Test',
        last_name='User',
        role='student',
        graduation_year=2024,
        major='Computer Science',
        is_active=True
    )
    user.set_password('password123')
    
    db_session.add(user)
    db_session.commit()
    
    return user


@pytest.fixture(scope='function')
def sample_alumni(db_session):
    """
    Create a sample alumni user for testing
    
    Args:
        db_session: Database session fixture
        
    Returns:
        User instance
    """
    from models import User
    
    user = User(
        email='alumni@pittstate.edu',
        first_name='Alumni',
        last_name='User',
        role='alumni',
        graduation_year=2020,
        major='Business',
        current_job_title='Software Engineer',
        current_company='Tech Corp',
        is_active=True
    )
    user.set_password('password123')
    
    db_session.add(user)
    db_session.commit()
    
    return user


@pytest.fixture(scope='function')
def sample_admin(db_session):
    """
    Create a sample admin user for testing
    
    Args:
        db_session: Database session fixture
        
    Returns:
        User instance
    """
    from models import User
    
    user = User(
        email='admin@pittstate.edu',
        first_name='Admin',
        last_name='User',
        role='admin',
        is_active=True
    )
    user.set_password('admin123')
    
    db_session.add(user)
    db_session.commit()
    
    return user


@pytest.fixture(scope='function')
def sample_job(db_session, sample_alumni):
    """
    Create a sample job posting for testing
    
    Args:
        db_session: Database session fixture
        sample_alumni: Alumni user fixture
        
    Returns:
        Job instance
    """
    from models import Job
    
    job = Job(
        title='Software Engineer',
        company='Tech Corp',
        location='Kansas City, MO',
        job_type='full_time',
        salary_min=60000,
        salary_max=80000,
        description='Great opportunity for software engineers',
        requirements='Bachelor degree in CS, 2+ years experience',
        posted_by=sample_alumni.id,
        posted_date=datetime.utcnow(),
        deadline=datetime.utcnow() + timedelta(days=30),
        is_active=True
    )
    
    db_session.add(job)
    db_session.commit()
    
    return job


@pytest.fixture(scope='function')
def sample_event(db_session):
    """
    Create a sample event for testing
    
    Args:
        db_session: Database session fixture
        
    Returns:
        Event instance
    """
    from models import Event
    
    event = Event(
        title='Career Fair 2024',
        description='Annual career fair for students and alumni',
        start_time=datetime.utcnow() + timedelta(days=7),
        end_time=datetime.utcnow() + timedelta(days=7, hours=4),
        location='Student Center',
        event_type='career_fair',
        capacity=200,
        is_virtual=False,
        is_active=True
    )
    
    db_session.add(event)
    db_session.commit()
    
    return event


@pytest.fixture(scope='function')
def sample_scholarship(db_session):
    """
    Create a sample scholarship for testing
    
    Args:
        db_session: Database session fixture
        
    Returns:
        Scholarship instance
    """
    from models import Scholarship
    
    scholarship = Scholarship(
        name='Excellence Scholarship',
        amount=5000.00,
        description='Scholarship for academic excellence',
        eligibility='Minimum 3.5 GPA',
        deadline=datetime.utcnow() + timedelta(days=60),
        requirements='Essay, transcript, recommendation letters',
        is_renewable=True,
        is_active=True
    )
    
    db_session.add(scholarship)
    db_session.commit()
    
    return scholarship


@pytest.fixture(scope='function')
def authenticated_client(client, sample_user):
    """
    Create an authenticated test client
    
    Args:
        client: Test client fixture
        sample_user: User fixture
        
    Returns:
        Authenticated test client
    """
    with client.session_transaction() as sess:
        sess['_user_id'] = str(sample_user.id)
        sess['_fresh'] = True
    
    return client


@pytest.fixture(scope='function')
def admin_client(client, sample_admin):
    """
    Create an admin authenticated test client
    
    Args:
        client: Test client fixture
        sample_admin: Admin user fixture
        
    Returns:
        Authenticated admin test client
    """
    with client.session_transaction() as sess:
        sess['_user_id'] = str(sample_admin.id)
        sess['_fresh'] = True
    
    return client


@pytest.fixture(scope='function')
def mock_redis():
    """
    Create a mock Redis client for testing
    
    Returns:
        Mock Redis instance
    """
    from unittest.mock import MagicMock
    
    redis_mock = MagicMock()
    redis_mock.get.return_value = None
    redis_mock.set.return_value = True
    redis_mock.delete.return_value = True
    redis_mock.zadd.return_value = True
    redis_mock.zremrangebyscore.return_value = True
    redis_mock.zcard.return_value = 0
    
    return redis_mock


@pytest.fixture(scope='function')
def mock_mail(app):
    """
    Create a mock mail sender for testing
    
    Args:
        app: Flask app fixture
        
    Returns:
        Mock mail instance
    """
    from unittest.mock import MagicMock
    from extensions import mail
    
    original_send = mail.send
    mail.send = MagicMock()
    
    yield mail
    
    mail.send = original_send


@pytest.fixture(scope='function')
def mock_openai():
    """
    Create a mock OpenAI client for testing
    
    Returns:
        Mock OpenAI instance
    """
    from unittest.mock import MagicMock, patch
    
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='This is a generated response'))
    ]
    
    with patch('openai.ChatCompletion.create', return_value=mock_response) as mock:
        yield mock


# Pytest configuration
def pytest_configure(config):
    """
    Configure pytest with custom markers
    
    Args:
        config: Pytest config object
    """
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )
