import pytest
from unittest.mock import MagicMock, AsyncMock, patch, call
from datetime import datetime

from src.bot.services.notification_service import NotificationService
from src.core.database import Database


class TestNotificationService:
    """Tests for the NotificationService class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_db = MagicMock(spec=Database)
        self.mock_app = MagicMock()
        self.mock_app.bot = MagicMock()
        self.mock_app.bot.send_message = AsyncMock()
        self.mock_app.logger = MagicMock()
        
        self.service = NotificationService(self.mock_db, self.mock_app)
        self.service.scheduler = MagicMock()
    
    def test_init(self):
        """Test initialization of NotificationService"""
        assert self.service.db == self.mock_db
        assert self.service.app == self.mock_app
        assert self.service.scheduler is not None
    
    def test_start(self):
        """Test start method"""
        self.service.start()
        self.service.scheduler.start.assert_called_once()
    
    def test_setup_daily_notifications(self):
        """Test setup_daily_notifications method"""
        # Mock database to return user IDs
        self.mock_db.get_all_users.return_value = [12345, 67890]
        
        # Call the method
        self.service.setup_daily_notifications()
        
        # Verify that scheduler.add_job was called for each user
        assert self.service.scheduler.add_job.call_count == 2
        
        # Check the first call
        args1, kwargs1 = self.service.scheduler.add_job.call_args_list[0]
        assert args1[0] == self.service.send_daily_notification
        assert kwargs1['args'] == [12345]
        assert kwargs1['id'] == "daily_12345"
        assert kwargs1['hour'] == 8
        assert kwargs1['minute'] == 0
        
        # Check the second call
        args2, kwargs2 = self.service.scheduler.add_job.call_args_list[1]
        assert args2[0] == self.service.send_daily_notification
        assert kwargs2['args'] == [67890]
        assert kwargs2['id'] == "daily_67890"
    
    @pytest.mark.asyncio
    @patch('src.bot.services.notification_service.Services')
    async def test_send_daily_notification(self, mock_services):
        """Test send_daily_notification method"""
        # Mock database to return zodiac sign
        self.mock_db.get_user_zodiac.return_value = "овен"
        
        # Mock services
        mock_services.get_weather.side_effect = ["Weather Moscow", "Weather Brest"]
        mock_services.get_exchange_rates.return_value = "Exchange Rates"
        mock_services.get_horoscope.return_value = "Horoscope for овен"
        mock_services.get_daily_quote.return_value = "Daily Quote"
        
        # Call the method
        await self.service.send_daily_notification(12345)
        
        # Verify that the services were called
        mock_services.get_weather.assert_has_calls([
            call("Moscow"),
            call("Brest,BY")
        ])
        mock_services.get_exchange_rates.assert_called_once()
        mock_services.get_horoscope.assert_called_once_with("овен")
        mock_services.get_daily_quote.assert_called_once()
        
        # Verify that send_message was called with the combined message
        self.mock_app.bot.send_message.assert_called_once()
        args, kwargs = self.mock_app.bot.send_message.call_args
        
        # Check that the message contains all the expected parts
        assert kwargs['chat_id'] == 12345
        assert "Доброе утро" in kwargs['text']
        assert "Weather Moscow" in kwargs['text']
        assert "Weather Brest" in kwargs['text']
        assert "Exchange Rates" in kwargs['text']
        assert "Horoscope for овен" in kwargs['text']
        assert "Daily Quote" in kwargs['text']
    
    @pytest.mark.asyncio
    @patch('src.bot.services.notification_service.Services')
    async def test_send_daily_notification_default_zodiac(self, mock_services):
        """Test send_daily_notification with default zodiac sign"""
        # Mock database to return no zodiac sign
        self.mock_db.get_user_zodiac.return_value = None
        
        # Mock services
        mock_services.get_weather.side_effect = ["Weather Moscow", "Weather Brest"]
        mock_services.get_exchange_rates.return_value = "Exchange Rates"
        mock_services.get_horoscope.return_value = "Horoscope for овен"
        mock_services.get_daily_quote.return_value = "Daily Quote"
        
        # Call the method
        await self.service.send_daily_notification(12345)
        
        # Verify that horoscope was called with default sign
        mock_services.get_horoscope.assert_called_once_with("овен")
    
    @pytest.mark.asyncio
    @patch('src.bot.services.notification_service.Services')
    async def test_send_daily_notification_error(self, mock_services):
        """Test send_daily_notification with error"""
        # Mock database to raise an exception
        self.mock_db.get_user_zodiac.side_effect = Exception("Database error")
        
        # Call the method
        await self.service.send_daily_notification(12345)
        
        # Verify that the error was logged
        self.mock_app.logger.error.assert_called_once()
        
        # Verify that send_message was not called
        self.mock_app.bot.send_message.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_send_medication_reminder(self):
        """Test send_medication_reminder method"""
        # Call the method
        await self.service.send_medication_reminder(12345, "Аспирин", 2)
        
        # Verify that send_message was called with the correct message
        self.mock_app.bot.send_message.assert_called_once()
        args, kwargs = self.mock_app.bot.send_message.call_args
        
        # Check the message
        assert kwargs['chat_id'] == 12345
        assert "Напоминание: примите 2 капсул(ы) Аспирин" in kwargs['text']
    
    @pytest.mark.asyncio
    async def test_send_medications_list_no_meds(self):
        """Test send_medications_list with no medications"""
        # Mock database to return no medications
        self.mock_db.get_medications.return_value = []
        
        # Call the method
        await self.service.send_medications_list(12345)
        
        # Verify that send_message was called with the correct message
        self.mock_app.bot.send_message.assert_called_once()
        args, kwargs = self.mock_app.bot.send_message.call_args
        
        # Check the message
        assert kwargs['chat_id'] == 12345
        assert "У вас пока нет добавленных лекарств" in kwargs['text']
    
    @pytest.mark.asyncio
    @patch('src.bot.services.notification_service.format_medication_info')
    async def test_send_medications_list_with_meds(self, mock_format):
        """Test send_medications_list with medications"""
        # Mock database to return medications
        med1 = (1, 12345, "Аспирин", 2, 3, "2025-01-01", 30, "days", 5, "days", 2)
        med2 = (2, 12345, "Витамин C", 1, 1, "2025-02-01", 60, "days", 0, "days", 1)
        self.mock_db.get_medications.return_value = [med1, med2]
        
        # Mock format_medication_info
        mock_format.side_effect = ["Formatted Med1", "Formatted Med2"]
        
        # Call the method
        await self.service.send_medications_list(12345)
        
        # Verify that format_medication_info was called for each medication
        assert mock_format.call_count == 2
        mock_format.assert_has_calls([call(med1), call(med2)])
        
        # Verify that send_message was called with the correct message
        self.mock_app.bot.send_message.assert_called_once()
        args, kwargs = self.mock_app.bot.send_message.call_args
        
        # Check the message
        assert kwargs['chat_id'] == 12345
        assert "Ваши лекарства" in kwargs['text']
        assert "Formatted Med1" in kwargs['text']
        assert "Formatted Med2" in kwargs['text']
        assert kwargs['parse_mode'] == "HTML"
    
    @pytest.mark.asyncio
    @patch('src.bot.services.notification_service.format_medication_info')
    async def test_send_medications_list_format_error(self, mock_format):
        """Test send_medications_list with formatting error"""
        # Mock database to return medications
        med1 = (1, 12345, "Аспирин", 2, 3, "2025-01-01", 30, "days", 5, "days", 2)
        self.mock_db.get_medications.return_value = [med1]
        
        # Mock format_medication_info to raise an exception
        mock_format.side_effect = Exception("Format error")
        
        # Call the method
        await self.service.send_medications_list(12345)
        
        # Verify that the error was logged
        self.mock_app.logger.error.assert_called_once()
        
        # Verify that send_message was called with an error message for the medication
        self.mock_app.bot.send_message.assert_called_once()
        args, kwargs = self.mock_app.bot.send_message.call_args
        
        # Check the message
        assert kwargs['chat_id'] == 12345
        assert "Ваши лекарства" in kwargs['text']
        assert "Лекарство ID 1 - ошибка данных" in kwargs['text']
        assert kwargs['parse_mode'] == "HTML"
    
    @pytest.mark.asyncio
    async def test_send_medications_list_db_error(self):
        """Test send_medications_list with database error"""
        # Mock database to raise an exception
        self.mock_db.get_medications.side_effect = Exception("Database error")
        
        # Call the method
        await self.service.send_medications_list(12345)
        
        # Verify that the error was logged
        self.mock_app.logger.error.assert_called_once()
        
        # Verify that send_message was called with an error message
        self.mock_app.bot.send_message.assert_called_once()
        args, kwargs = self.mock_app.bot.send_message.call_args
        
        # Check the message
        assert kwargs['chat_id'] == 12345
        assert "Произошла ошибка при загрузке данных" in kwargs['text']
    
    @pytest.mark.asyncio
    async def test_send_message(self):
        """Test _send_message method"""
        # Call the method
        await self.service._send_message(12345, "Test message", parse_mode="HTML")
        
        # Verify that send_message was called with the correct parameters
        self.mock_app.bot.send_message.assert_called_once_with(
            chat_id=12345,
            text="Test message",
            parse_mode="HTML"
        )
    
    @pytest.mark.asyncio
    async def test_send_message_error(self):
        """Test _send_message with error"""
        # Mock send_message to raise an exception
        self.mock_app.bot.send_message.side_effect = Exception("Send error")
        
        # Call the method
        await self.service._send_message(12345, "Test message")
        
        # Verify that the error was logged
        self.mock_app.logger.error.assert_called_once()
