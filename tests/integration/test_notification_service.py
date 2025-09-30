import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from src.bot.services.notification_service import NotificationService


class TestNotificationService:
    """Tests for the NotificationService class"""
    
    def test_init(self, mock_db, mock_bot_app):
        """Test initialization of NotificationService"""
        service = NotificationService(mock_db, mock_bot_app)
        
        assert service.db == mock_db
        assert service.app == mock_bot_app
        assert service.scheduler is not None
    
    def test_start(self, mock_db, mock_bot_app):
        """Test starting the scheduler"""
        service = NotificationService(mock_db, mock_bot_app)
        
        # Mock the scheduler's start method
        service.scheduler.start = MagicMock()
        
        service.start()
        
        # Verify that scheduler.start was called
        service.scheduler.start.assert_called_once()
    
    def test_setup_daily_notifications(self, mock_db, mock_bot_app):
        """Test setting up daily notifications"""
        service = NotificationService(mock_db, mock_bot_app)
        
        # Mock the scheduler's add_job method
        service.scheduler.add_job = MagicMock()
        
        # Mock the database's get_all_users method to return some users
        mock_db.get_all_users.return_value = [12345, 67890]
        
        service.setup_daily_notifications()
        
        # Verify that add_job was called for each user
        assert service.scheduler.add_job.call_count == 2
        
        # Check the first call
        args, kwargs = service.scheduler.add_job.call_args_list[0]
        assert args[0] == service.send_daily_notification  # Function to call
        assert kwargs['hour'] == 8  # Hour to send notification
        assert kwargs['minute'] == 0  # Minute to send notification
        assert kwargs['args'] == [12345]  # User ID
        assert kwargs['id'] == "daily_12345"  # Job ID
        
        # Check the second call
        args, kwargs = service.scheduler.add_job.call_args_list[1]
        assert args[0] == service.send_daily_notification  # Function to call
        assert kwargs['hour'] == 8  # Hour to send notification
        assert kwargs['minute'] == 0  # Minute to send notification
        assert kwargs['args'] == [67890]  # User ID
        assert kwargs['id'] == "daily_67890"  # Job ID
    
    @pytest.mark.asyncio
    async def test_send_daily_notification(self, mock_db, mock_bot_app):
        """Test sending daily notification"""
        service = NotificationService(mock_db, mock_bot_app)
        
        # Mock the database's get_user_zodiac method
        mock_db.get_user_zodiac.return_value = "овен"
        
        # Mock the Services class methods
        with patch('src.utils.services.Services') as mock_services:
            mock_services.get_weather.return_value = "Weather info"
            mock_services.get_exchange_rates.return_value = "Exchange rates"
            mock_services.get_horoscope.return_value = "Horoscope for овен"
            mock_services.get_daily_quote.return_value = "Daily quote"
            
            # Mock the _send_message method
            service._send_message = AsyncMock()
            
            # Call the method
            await service.send_daily_notification(12345)
            
            # Verify that _send_message was called with the correct arguments
            service._send_message.assert_called_once()
            args, kwargs = service._send_message.call_args
            
            # Check that the user ID is correct
            assert args[0] == 12345
            
            # Check that the message contains all the expected parts
            message = args[1]
            assert "Доброе утро" in message
            assert "Weather info" in message
            assert "Exchange rates" in message
            assert "Horoscope for овен" in message
            assert "Daily quote" in message
    
    @pytest.mark.asyncio
    async def test_send_daily_notification_error(self, mock_db, mock_bot_app):
        """Test error handling in send_daily_notification"""
        service = NotificationService(mock_db, mock_bot_app)
        
        # Mock the database's get_user_zodiac method to raise an exception
        mock_db.get_user_zodiac.side_effect = Exception("Test error")
        
        # Call the method
        await service.send_daily_notification(12345)
        
        # Verify that the error was logged
        mock_bot_app.logger.error.assert_called_once()
        args, kwargs = mock_bot_app.logger.error.call_args
        assert "Ошибка отправки ежедневного уведомления" in args[0]
    
    @pytest.mark.asyncio
    async def test_send_medication_reminder(self, mock_db, mock_bot_app):
        """Test sending medication reminder"""
        service = NotificationService(mock_db, mock_bot_app)
        
        # Mock the _send_message method
        service._send_message = AsyncMock()
        
        # Call the method
        await service.send_medication_reminder(12345, "Test Med", 2)
        
        # Verify that _send_message was called with the correct arguments
        service._send_message.assert_called_once()
        args, kwargs = service._send_message.call_args
        
        # Check that the user ID is correct
        assert args[0] == 12345
        
        # Check that the message contains the medication name and dose
        message = args[1]
        assert "Test Med" in message
        assert "2" in message
    
    @pytest.mark.asyncio
    async def test_send_medications_list_empty(self, mock_db, mock_bot_app):
        """Test sending medications list when empty"""
        service = NotificationService(mock_db, mock_bot_app)
        
        # Mock the database's get_medications method to return empty list
        mock_db.get_medications.return_value = []
        
        # Mock the _send_message method
        service._send_message = AsyncMock()
        
        # Call the method
        await service.send_medications_list(12345)
        
        # Verify that _send_message was called with the correct arguments
        service._send_message.assert_called_once()
        args, kwargs = service._send_message.call_args
        
        # Check that the user ID is correct
        assert args[0] == 12345
        
        # Check that the message indicates no medications
        message = args[1]
        assert "У вас пока нет добавленных лекарств" in message
    
    @pytest.mark.asyncio
    async def test_send_medications_list(self, mock_db, mock_bot_app, sample_medication_tuple):
        """Test sending medications list"""
        service = NotificationService(mock_db, mock_bot_app)
        
        # Mock the database's get_medications method to return a medication
        mock_db.get_medications.return_value = [sample_medication_tuple]
        
        # Mock the _send_message method
        service._send_message = AsyncMock()
        
        # Call the method
        await service.send_medications_list(12345)
        
        # Verify that _send_message was called with the correct arguments
        service._send_message.assert_called_once()
        args, kwargs = service._send_message.call_args
        
        # Check that the user ID is correct
        assert args[0] == 12345
        
        # Check that the message contains the medication name
        message = args[1]
        assert "Test Medication" in message
        
        # Check that parse_mode is HTML
        assert kwargs.get('parse_mode') == "HTML"
    
    @pytest.mark.asyncio
    async def test_send_medications_list_error(self, mock_db, mock_bot_app):
        """Test error handling in send_medications_list"""
        service = NotificationService(mock_db, mock_bot_app)
        
        # Mock the database's get_medications method to raise an exception
        mock_db.get_medications.side_effect = Exception("Test error")
        
        # Mock the _send_message method
        service._send_message = AsyncMock()
        
        # Call the method
        await service.send_medications_list(12345)
        
        # Verify that the error was logged
        mock_bot_app.logger.error.assert_called_once()
        
        # Verify that _send_message was called with an error message
        service._send_message.assert_called_once()
        args, kwargs = service._send_message.call_args
        
        # Check that the user ID is correct
        assert args[0] == 12345
        
        # Check that the message indicates an error
        message = args[1]
        assert "Произошла ошибка при загрузке данных" in message
    
    @pytest.mark.asyncio
    async def test_send_message(self, mock_db, mock_bot_app):
        """Test sending a message"""
        service = NotificationService(mock_db, mock_bot_app)
        
        # Call the method
        await service._send_message(12345, "Test message", parse_mode="HTML")
        
        # Verify that the bot's send_message method was called with the correct arguments
        mock_bot_app.bot.send_message.assert_called_once_with(
            chat_id=12345,
            text="Test message",
            parse_mode="HTML"
        )
    
    @pytest.mark.asyncio
    async def test_send_message_error(self, mock_db, mock_bot_app):
        """Test error handling in _send_message"""
        service = NotificationService(mock_db, mock_bot_app)
        
        # Mock the bot's send_message method to raise an exception
        mock_bot_app.bot.send_message.side_effect = Exception("Test error")
        
        # Call the method
        await service._send_message(12345, "Test message")
        
        # Verify that the error was logged
        mock_bot_app.logger.error.assert_called_once()
        args, kwargs = mock_bot_app.logger.error.call_args
        assert "Ошибка отправки сообщения" in args[0]
