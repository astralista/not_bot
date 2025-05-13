import os
import pytest
import sqlite3
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from src.core.database import Database
from src.bot.models.medication import Medication
from src.bot.models.user import User


@pytest.fixture
def mock_db():
    """
    Fixture for mocking the Database class
    """
    db = MagicMock(spec=Database)
    
    # Mock methods
    db.get_medications.return_value = []
    db.get_medication_by_id.return_value = None
    db.get_all_medications.return_value = []
    db.get_all_users.return_value = []
    db.get_user_zodiac.return_value = None
    
    return db


@pytest.fixture
def mock_bot_app():
    """
    Fixture for mocking the bot application
    """
    app = MagicMock()
    app.bot = MagicMock()
    app.bot.send_message = AsyncMock()
    app.logger = MagicMock()
    
    return app


@pytest.fixture
def mock_update():
    """
    Fixture for mocking the Update object from python-telegram-bot
    """
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 12345
    update.message = MagicMock()
    update.message.from_user = MagicMock()
    update.message.from_user.id = 12345
    update.message.reply_text = AsyncMock()
    update.callback_query = MagicMock()
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    
    return update


@pytest.fixture
def mock_context():
    """
    Fixture for mocking the Context object from python-telegram-bot
    """
    context = MagicMock()
    context.user_data = {}
    context.args = []
    
    return context


@pytest.fixture
def sample_medication():
    """
    Fixture for creating a sample Medication object
    """
    return Medication(
        id=1,
        user_id=12345,
        name="Test Medication",
        dose_per_intake=2,
        intakes_per_day=3,
        start_date="2025-01-01",
        duration_value=10,
        duration_unit="days",
        break_value=5,
        break_unit="days",
        cycles=2
    )


@pytest.fixture
def sample_medication_tuple():
    """
    Fixture for creating a sample medication tuple (as returned from DB)
    """
    return (
        1,                  # id
        12345,              # user_id
        "Test Medication",  # name
        2,                  # dose_per_intake
        3,                  # intakes_per_day
        "2025-01-01",       # start_date
        10,                 # duration_value
        "days",             # duration_unit
        5,                  # break_value
        "days",             # break_unit
        2                   # cycles
    )


@pytest.fixture
def sample_user():
    """
    Fixture for creating a sample User object
    """
    return User(
        user_id=12345,
        zodiac_sign="овен"
    )


@pytest.fixture
def in_memory_db():
    """
    Fixture for creating an in-memory SQLite database for testing
    """
    db = Database(":memory:")
    yield db
    # No need to close the connection as it's in-memory
