import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.bot.handlers.notification_handlers import NotificationHandlers


class TestNotificationHandlers:
    """Tests for the NotificationHandlers class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_db = MagicMock()
        self.mock_logger = MagicMock()
        self.handlers = NotificationHandlers(self.mock_db, self.mock_logger)
    
    @pytest.mark.asyncio
    async def test_set_zodiac_with_args(self, mock_update, mock_context):
        """Test set_zodiac command with valid arguments"""
        # Set up the context args
        mock_context.args = ["овен"]
        
        # Call the method
        await self.handlers.set_zodiac(mock_update, mock_context)
        
        # Verify that the database was updated with the correct user ID and zodiac sign
        self.mock_db.add_user_settings.assert_called_once_with(mock_update.effective_user.id, "овен")
        
        # Verify that a confirmation reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message confirms the zodiac sign
        assert "Ваш знак зодиака сохранён: Овен" in args[0]
    
    @pytest.mark.asyncio
    async def test_set_zodiac_with_multiple_word_args(self, mock_update, mock_context):
        """Test set_zodiac command with multi-word zodiac sign"""
        # Set up the context args
        mock_context.args = ["водолей"]
        
        # Call the method
        await self.handlers.set_zodiac(mock_update, mock_context)
        
        # Verify that the database was updated with the correct user ID and zodiac sign
        self.mock_db.add_user_settings.assert_called_once_with(mock_update.effective_user.id, "водолей")
        
        # Verify that a confirmation reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message confirms the zodiac sign
        assert "Ваш знак зодиака сохранён: Водолей" in args[0]
    
    @pytest.mark.asyncio
    async def test_set_zodiac_with_invalid_args(self, mock_update, mock_context):
        """Test set_zodiac command with invalid zodiac sign"""
        # Set up the context args
        mock_context.args = ["invalid"]
        
        # Call the method
        await self.handlers.set_zodiac(mock_update, mock_context)
        
        # Verify that the database was not updated
        self.mock_db.add_user_settings.assert_not_called()
        
        # Verify that an error reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates an error
        assert "Неверный знак зодиака" in args[0]
    
    @pytest.mark.asyncio
    async def test_set_zodiac_without_args(self, mock_update, mock_context):
        """Test set_zodiac command without arguments"""
        # Set up the context args
        mock_context.args = []
        
        # Call the method
        await self.handlers.set_zodiac(mock_update, mock_context)
        
        # Verify that the database was not updated
        self.mock_db.add_user_settings.assert_not_called()
        
        # Verify that a help reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message provides usage instructions
        assert "Укажите ваш знак зодиака после команды" in args[0]
    
    @pytest.mark.asyncio
    async def test_set_zodiac_database_error(self, mock_update, mock_context):
        """Test database error when setting zodiac sign"""
        # Set up the context args
        mock_context.args = ["овен"]
        
        # Mock the database to raise an exception
        self.mock_db.add_user_settings.side_effect = Exception("Database error")
        
        # Call the method
        await self.handlers.set_zodiac(mock_update, mock_context)
        
        # Verify that an error reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates an error
        assert "Произошла ошибка при сохранении" in args[0]
        
        # Check that the error was logged
        self.mock_logger.getChild().error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_toggle_notifications(self, mock_update, mock_context):
        """Test toggle_notifications command"""
        # Call the method
        await self.handlers.toggle_notifications(mock_update, mock_context)
        
        # Verify that a reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message confirms notifications are enabled
        assert "Уведомления включены" in args[0]
    
    @pytest.mark.asyncio
    async def test_set_notification_time(self, mock_update, mock_context):
        """Test set_notification_time command"""
        # Call the method
        await self.handlers.set_notification_time(mock_update, mock_context)
        
        # Verify that a reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message confirms the notification time
        assert "Время ежедневных уведомлений установлено" in args[0]
