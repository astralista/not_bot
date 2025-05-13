import pytest
from unittest.mock import MagicMock, AsyncMock, patch, call
from datetime import datetime, timedelta

from src.bot.services.scheduler_service import SchedulerService
from src.core.database import Database


class TestSchedulerService:
    """Tests for the SchedulerService class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_db = MagicMock(spec=Database)
        self.mock_app = MagicMock()
        self.mock_app.bot = MagicMock()
        self.mock_app.bot.send_message = AsyncMock()
        self.mock_app.logger = MagicMock()
        
        self.service = SchedulerService(self.mock_db, self.mock_app)
        self.service.scheduler = MagicMock()
    
    def test_init(self):
        """Test initialization of SchedulerService"""
        assert self.service.db == self.mock_db
        assert self.service.app == self.mock_app
        assert self.service.scheduler is not None
    
    def test_start(self):
        """Test start method"""
        self.service.start()
        self.service.scheduler.start.assert_called_once()
    
    def test_setup_medication_checks(self):
        """Test setup_medication_checks method"""
        # Call the method
        self.service.setup_medication_checks()
        
        # Verify that scheduler.add_job was called with the correct parameters
        self.service.scheduler.add_job.assert_called_once()
        args, kwargs = self.service.scheduler.add_job.call_args
        
        # Check the arguments
        assert args[0] == self.service.check_medications
        assert kwargs['minutes'] == 30
        assert kwargs['id'] == "medication_check"
    
    @pytest.mark.asyncio
    @patch('src.bot.services.scheduler_service.datetime')
    @patch('src.bot.services.scheduler_service.calculate_next_notification')
    async def test_check_medications_active(self, mock_calculate, mock_datetime):
        """Test check_medications with active medication"""
        # Mock current time
        now = datetime(2025, 1, 15, 9, 0)  # 9:00 AM
        mock_datetime.now.return_value = now
        
        # Mock database to return medications
        med = (1, 12345, "Аспирин", 2, 1, "2025-01-01", 30, "days", 5, "days", 2)
        self.mock_db.get_all_medications.return_value = [med]
        
        # Mock calculate_next_notification to return notification times
        notification_time = datetime(2025, 1, 15, 9, 0)  # 9:00 AM
        mock_calculate.return_value = [notification_time]
        
        # Call the method
        await self.service.check_medications()
        
        # Verify that get_all_medications was called
        self.mock_db.get_all_medications.assert_called_once()
        
        # Verify that calculate_next_notification was called with the correct parameters
        mock_calculate.assert_called_once()
        args, kwargs = mock_calculate.call_args
        assert args[0] == datetime(2025, 1, 1).date()
        assert args[1] == 1
        
        # Verify that send_medication_reminder was called
        self.mock_app.bot.send_message.assert_called_once()
        args, kwargs = self.mock_app.bot.send_message.call_args
        
        # Check the message
        assert kwargs['chat_id'] == 12345
        assert "Напоминание: примите 2 капсул(ы) Аспирин" in kwargs['text']
    
    @pytest.mark.asyncio
    @patch('src.bot.services.scheduler_service.datetime')
    @patch('src.bot.services.scheduler_service.calculate_next_notification')
    async def test_check_medications_not_started(self, mock_calculate, mock_datetime):
        """Test check_medications with medication not started yet"""
        # Mock current time
        now = datetime(2025, 1, 15, 9, 0)  # 9:00 AM
        mock_datetime.now.return_value = now
        
        # Mock database to return medications
        med = (1, 12345, "Аспирин", 2, 1, "2025-02-01", 30, "days", 5, "days", 2)  # Starts Feb 1
        self.mock_db.get_all_medications.return_value = [med]
        
        # Call the method
        await self.service.check_medications()
        
        # Verify that get_all_medications was called
        self.mock_db.get_all_medications.assert_called_once()
        
        # Verify that calculate_next_notification was not called
        mock_calculate.assert_not_called()
        
        # Verify that send_medication_reminder was not called
        self.mock_app.bot.send_message.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('src.bot.services.scheduler_service.datetime')
    @patch('src.bot.services.scheduler_service.calculate_next_notification')
    async def test_check_medications_ended(self, mock_calculate, mock_datetime):
        """Test check_medications with medication already ended"""
        # Mock current time
        now = datetime(2025, 3, 15, 9, 0)  # March 15, 9:00 AM
        mock_datetime.now.return_value = now
        
        # Mock database to return medications
        med = (1, 12345, "Аспирин", 2, 1, "2025-01-01", 30, "days", 5, "days", 2)  # Ended Jan 31
        self.mock_db.get_all_medications.return_value = [med]
        
        # Call the method
        await self.service.check_medications()
        
        # Verify that get_all_medications was called
        self.mock_db.get_all_medications.assert_called_once()
        
        # Verify that calculate_next_notification was not called
        mock_calculate.assert_not_called()
        
        # Verify that send_medication_reminder was not called
        self.mock_app.bot.send_message.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('src.bot.services.scheduler_service.datetime')
    @patch('src.bot.services.scheduler_service.calculate_next_notification')
    async def test_check_medications_wrong_time(self, mock_calculate, mock_datetime):
        """Test check_medications with wrong notification time"""
        # Mock current time
        now = datetime(2025, 1, 15, 10, 0)  # 10:00 AM
        mock_datetime.now.return_value = now
        
        # Mock database to return medications
        med = (1, 12345, "Аспирин", 2, 1, "2025-01-01", 30, "days", 5, "days", 2)
        self.mock_db.get_all_medications.return_value = [med]
        
        # Mock calculate_next_notification to return notification times
        notification_time = datetime(2025, 1, 15, 9, 0)  # 9:00 AM
        mock_calculate.return_value = [notification_time]
        
        # Call the method
        await self.service.check_medications()
        
        # Verify that get_all_medications was called
        self.mock_db.get_all_medications.assert_called_once()
        
        # Verify that calculate_next_notification was called
        mock_calculate.assert_called_once()
        
        # Verify that send_medication_reminder was not called
        self.mock_app.bot.send_message.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('src.bot.services.scheduler_service.datetime')
    @patch('src.bot.services.scheduler_service.calculate_next_notification')
    async def test_check_medications_within_window(self, mock_calculate, mock_datetime):
        """Test check_medications with time within notification window"""
        # Mock current time
        now = datetime(2025, 1, 15, 9, 10)  # 9:10 AM
        mock_datetime.now.return_value = now
        
        # Mock database to return medications
        med = (1, 12345, "Аспирин", 2, 1, "2025-01-01", 30, "days", 5, "days", 2)
        self.mock_db.get_all_medications.return_value = [med]
        
        # Mock calculate_next_notification to return notification times
        notification_time = datetime(2025, 1, 15, 9, 0)  # 9:00 AM
        mock_calculate.return_value = [notification_time]
        
        # Call the method
        await self.service.check_medications()
        
        # Verify that get_all_medications was called
        self.mock_db.get_all_medications.assert_called_once()
        
        # Verify that calculate_next_notification was called
        mock_calculate.assert_called_once()
        
        # Verify that send_medication_reminder was called
        self.mock_app.bot.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.bot.services.scheduler_service.datetime')
    @patch('src.bot.services.scheduler_service.calculate_next_notification')
    async def test_check_medications_multiple_intakes(self, mock_calculate, mock_datetime):
        """Test check_medications with multiple intakes per day"""
        # Mock current time
        now = datetime(2025, 1, 15, 9, 0)  # 9:00 AM
        mock_datetime.now.return_value = now
        
        # Mock database to return medications
        med = (1, 12345, "Аспирин", 2, 3, "2025-01-01", 30, "days", 5, "days", 2)  # 3 intakes per day
        self.mock_db.get_all_medications.return_value = [med]
        
        # Mock calculate_next_notification to return notification times
        notification_times = [
            datetime(2025, 1, 15, 9, 0),  # 9:00 AM
            datetime(2025, 1, 15, 15, 0),  # 3:00 PM
            datetime(2025, 1, 15, 21, 0)   # 9:00 PM
        ]
        mock_calculate.return_value = notification_times
        
        # Call the method
        await self.service.check_medications()
        
        # Verify that get_all_medications was called
        self.mock_db.get_all_medications.assert_called_once()
        
        # Verify that calculate_next_notification was called
        mock_calculate.assert_called_once()
        
        # Verify that send_medication_reminder was called
        self.mock_app.bot.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.bot.services.scheduler_service.datetime')
    async def test_check_medications_error(self, mock_datetime):
        """Test check_medications with error"""
        # Mock current time
        now = datetime(2025, 1, 15, 9, 0)  # 9:00 AM
        mock_datetime.now.return_value = now
        
        # Mock database to raise an exception
        self.mock_db.get_all_medications.side_effect = Exception("Database error")
        
        # Call the method
        await self.service.check_medications()
        
        # Verify that the error was logged
        self.mock_app.logger.error.assert_called_once()
        
        # Verify that send_medication_reminder was not called
        self.mock_app.bot.send_message.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('src.bot.services.scheduler_service.datetime')
    @patch('src.bot.services.scheduler_service.calculate_next_notification')
    async def test_check_medications_processing_error(self, mock_calculate, mock_datetime):
        """Test check_medications with error during medication processing"""
        # Mock current time
        now = datetime(2025, 1, 15, 9, 0)  # 9:00 AM
        mock_datetime.now.return_value = now
        
        # Mock database to return medications
        med = (1, 12345, "Аспирин", 2, 1, "invalid-date", 30, "days", 5, "days", 2)  # Invalid date
        self.mock_db.get_all_medications.return_value = [med]
        
        # Call the method
        await self.service.check_medications()
        
        # Verify that get_all_medications was called
        self.mock_db.get_all_medications.assert_called_once()
        
        # Verify that the error was logged
        self.mock_app.logger.error.assert_called_once()
        
        # Verify that send_medication_reminder was not called
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
    async def test_send_medication_reminder_error(self):
        """Test send_medication_reminder with error"""
        # Mock send_message to raise an exception
        self.mock_app.bot.send_message.side_effect = Exception("Send error")
        
        # Call the method
        await self.service.send_medication_reminder(12345, "Аспирин", 2)
        
        # Verify that the error was logged
        self.mock_app.logger.error.assert_called_once()
