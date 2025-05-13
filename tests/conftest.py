import pytest
import sqlite3
from unittest.mock import MagicMock, AsyncMock
from telegram import Update, User, Message, Chat, CallbackQuery
from telegram.ext import ContextTypes

from src.core.database import Database


@pytest.fixture
def in_memory_db():
    """Create an in-memory database for testing"""
    db = Database(":memory:")
    return db


@pytest.fixture
def mock_update():
    """Create a mock Update object for testing"""
    update = MagicMock(spec=Update)
    
    # Mock user
    user = MagicMock(spec=User)
    user.id = 12345
    user.first_name = "Test"
    user.last_name = "User"
    user.username = "testuser"
    
    # Mock chat
    chat = MagicMock(spec=Chat)
    chat.id = 12345
    
    # Mock message
    message = MagicMock(spec=Message)
    message.from_user = user
    message.chat = chat
    message.text = "Test message"
    message.reply_text = AsyncMock()
    
    # Mock callback query
    callback_query = MagicMock(spec=CallbackQuery)
    callback_query.from_user = user
    callback_query.message = message
    callback_query.data = "test_data"
    callback_query.answer = AsyncMock()
    callback_query.edit_message_text = AsyncMock()
    
    # Set up the update object
    update.effective_user = user
    update.message = message
    update.callback_query = callback_query
    
    return update


@pytest.fixture
def mock_context():
    """Create a mock Context object for testing"""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    context.args = []
    
    return context
