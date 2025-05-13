import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.bot.handlers.notification_handlers import NotificationHandlers


class TestNotificationHandlers:
    """Tests for the NotificationHandlers class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_db = MagicMock()
        self.mock_logger = MagicMock()
        self.handlers = NotificationHandlers(self.mock_db, self.mock_logger)
    
    @pytest.mark.asyncio
    async def test_set_zodiac_no_args(self, mock_update, mock_context):
        """Test set_zodiac with no arguments"""
        # Set up the context with no args
        mock_context.args = []
        
        # Call the method
        await self.handlers.set_zodiac(mock_update, mock_context)
        
        # Verify that a reply was sent with instructions
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message contains instructions
        assert "Укажите ваш знак зодиака после команды" in args[0]
        assert "/set_zodiac овен" in args[0]
        assert "Доступные знаки" in args[0]
    
    @pytest.mark.asyncio
    async def test_set_zodiac_invalid_sign(self, mock_update, mock_context):
        """Test set_zodiac with invalid zodiac sign"""
        # Set up the context with invalid args
        mock_context.args = ["invalid_sign"]
        
        # Call the method
        await self.handlers.set_zodiac(mock_update, mock_context)
        
        # Verify that a reply was sent with an error message
        mock_update.message.reply_text.assert_called_once_with("Неверный знак зодиака!")
        
        # Verify that the database was not updated
        self.mock_db.add_user_settings.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_set_zodiac_valid_sign(self, mock_update, mock_context):
        """Test set_zodiac with valid zodiac sign"""
        # Set up the context with valid args
        mock_context.args = ["овен"]
        
        # Call the method
        await self.handlers.set_zodiac(mock_update, mock_context)
        
        # Verify that the database was updated with the correct values
        self.mock_db.add_user_settings.assert_called_once_with(mock_update.effective_user.id, "овен")
        
        # Verify that a reply was sent with a success message
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message contains the confirmation
        assert "Ваш знак зодиака сохранён: Овен" in args[0]
        assert "персональный гороскоп" in args[0]
    
    @pytest.mark.asyncio
    async def test_set_zodiac_multiple_words(self, mock_update, mock_context):
        """Test set_zodiac with multi-word zodiac sign"""
        # Set up the context with valid args
        mock_context.args = ["близнецы"]
        
        # Call the method
        await self.handlers.set_zodiac(mock_update, mock_context)
        
        # Verify that the database was updated with the correct values
        self.mock_db.add_user_settings.assert_called_once_with(mock_update.effective_user.id, "близнецы")
        
        # Verify that a reply was sent with a success message
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message contains the confirmation
        assert "Ваш знак зодиака сохранён: Близнецы" in args[0]
    
    @pytest.mark.asyncio
    async def test_set_zodiac_database_error(self, mock_update, mock_context):
        """Test set_zodiac with database error"""
        # Set up the context with valid args
        mock_context.args = ["овен"]
        
        # Mock the database to raise an exception
        self.mock_db.add_user_settings.side_effect = Exception("Database error")
        
        # Call the method
        await self.handlers.set_zodiac(mock_update, mock_context)
        
        # Verify that the database was called
        self.mock_db.add_user_settings.assert_called_once()
        
        # Verify that the error was logged
        self.mock_logger.getChild().error.assert_called_once()
        
        # Verify that a reply was sent with an error message
        mock_update.message.reply_text.assert_called_once_with("Произошла ошибка при сохранении.")
    
    @pytest.mark.asyncio
    async def test_toggle_notifications(self, mock_update, mock_context):
        """Test toggle_notifications method"""
        # Call the method
        await self.handlers.toggle_notifications(mock_update, mock_context)
        
        # Verify that a reply was sent with the notification status
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message contains the notification status
        assert "Уведомления включены" in args[0]
        assert "напоминания о приеме лекарств" in args[0]
    
    @pytest.mark.asyncio
    async def test_set_notification_time(self, mock_update, mock_context):
        """Test set_notification_time method"""
        # Call the method
        await self.handlers.set_notification_time(mock_update, mock_context)
        
        # Verify that a reply was sent with the notification time
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message contains the notification time
        assert "Время ежедневных уведомлений установлено" in args[0]
        assert "9:00" in args[0]
