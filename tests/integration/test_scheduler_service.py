import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta
from freezegun import freeze_time

from src.bot.services.scheduler_service import SchedulerService


class TestSchedulerService:
    """Tests for the SchedulerService class"""
    
    def test_init(self, mock_db, mock_bot_app):
        """Test initialization of SchedulerService"""
        service = SchedulerService(mock_db, mock_bot_app)
        
        assert service.db == mock_db
        assert service.app == mock_bot_app
        assert service.scheduler is not None
    
    def test_start(self, mock_db, mock_bot_app):
        """Test starting the scheduler"""
        service = SchedulerService(mock_db, mock_bot_app)
        
        # Mock the scheduler's start method
        service.scheduler.start = MagicMock()
        
        service.start()
        
        # Verify that scheduler.start was called
        service.scheduler.start.assert_called_once()
    
    def test_setup_medication_checks(self, mock_db, mock_bot_app):
        """Test setting up medication checks"""
        service = SchedulerService(mock_db, mock_bot_app)
        
        # Mock the scheduler's add_job method
        service.scheduler.add_job = MagicMock()
        
        service.setup_medication_checks()
        
        # Verify that add_job was called with the correct arguments
        service.scheduler.add_job.assert_called_once()
        args, kwargs = service.scheduler.add_job.call_args
        
        assert args[0] == service.check_medications  # Function to call
        assert kwargs['minutes'] == 30  # Check every 30 minutes
        assert kwargs['id'] == "medication_check"  # Job ID
    
    @pytest.mark.asyncio
    @freeze_time("2025-01-15 09:00:00")
    async def test_check_medications_active(self, mock_db, mock_bot_app, sample_medication_tuple):
        """Test checking active medications"""
        service = SchedulerService(mock_db, mock_bot_app)
        
        # Mock the database's get_all_medications method to return a medication
        # This medication is active (current date is within the duration)
        mock_db.get_all_medications.return_value = [sample_medication_tuple]
        
        # Mock the send_medication_reminder method
        service.send_medication_reminder = AsyncMock()
        
        # Mock the calculate_next_notification function to return notification times
        with patch('src.utils.helpers.calculate_next_notification') as mock_calc:
            # Return notification times that include the current hour
            mock_calc.return_value = [
                datetime(2025, 1, 15, 9, 0),  # 9:00 AM - matches current time
                datetime(2025, 1, 15, 15, 0),  # 3:00 PM
                datetime(2025, 1, 15, 21, 0)   # 9:00 PM
            ]
            
            # Call the method
            await service.check_medications()
            
            # Verify that send_medication_reminder was called
            service.send_medication_reminder.assert_called_once_with(
                12345,  # user_id from sample_medication_tuple
                "Test Medication",  # name from sample_medication_tuple
                2  # dose_per_intake from sample_medication_tuple
            )
    
    @pytest.mark.asyncio
    @freeze_time("2025-01-15 10:00:00")
    async def test_check_medications_no_match(self, mock_db, mock_bot_app, sample_medication_tuple):
        """Test checking medications with no matching notification time"""
        service = SchedulerService(mock_db, mock_bot_app)
        
        # Mock the database's get_all_medications method to return a medication
        mock_db.get_all_medications.return_value = [sample_medication_tuple]
        
        # Mock the send_medication_reminder method
        service.send_medication_reminder = AsyncMock()
        
        # Mock the calculate_next_notification function to return notification times
        with patch('src.utils.helpers.calculate_next_notification') as mock_calc:
            # Return notification times that don't include the current hour
            mock_calc.return_value = [
                datetime(2025, 1, 15, 9, 0),   # 9:00 AM
                datetime(2025, 1, 15, 15, 0),  # 3:00 PM
                datetime(2025, 1, 15, 21, 0)   # 9:00 PM
            ]
            
            # Call the method
            await service.check_medications()
            
            # Verify that send_medication_reminder was not called
            service.send_medication_reminder.assert_not_called()
    
    @pytest.mark.asyncio
    @freeze_time("2024-12-15 09:00:00")
    async def test_check_medications_not_started(self, mock_db, mock_bot_app):
        """Test checking medications that haven't started yet"""
        service = SchedulerService(mock_db, mock_bot_app)
        
        # Create a medication that starts in the future
        future_med = (
            1,                  # id
            12345,              # user_id
            "Future Med",       # name
            2,                  # dose_per_intake
            3,                  # intakes_per_day
            "2025-01-01",       # start_date (future)
            30,                 # duration_value
            "days",             # duration_unit
            5,                  # break_value
            "days",             # break_unit
            2                   # cycles
        )
        
        # Mock the database's get_all_medications method
        mock_db.get_all_medications.return_value = [future_med]
        
        # Mock the send_medication_reminder method
        service.send_medication_reminder = AsyncMock()
        
        # Call the method
        await service.check_medications()
        
        # Verify that send_medication_reminder was not called
        service.send_medication_reminder.assert_not_called()
    
    @pytest.mark.asyncio
    @freeze_time("2025-03-15 09:00:00")
    async def test_check_medications_ended(self, mock_db, mock_bot_app):
        """Test checking medications that have ended"""
        service = SchedulerService(mock_db, mock_bot_app)
        
        # Create a medication that has ended
        past_med = (
            1,                  # id
            12345,              # user_id
            "Past Med",         # name
            2,                  # dose_per_intake
            3,                  # intakes_per_day
            "2025-01-01",       # start_date
            30,                 # duration_value
            "days",             # duration_unit
            5,                  # break_value
            "days",             # break_unit
            1                   # cycles
        )
        
        # Mock the database's get_all_medications method
        mock_db.get_all_medications.return_value = [past_med]
        
        # Mock the send_medication_reminder method
        service.send_medication_reminder = AsyncMock()
        
        # Call the method
        await service.check_medications()
        
        # Verify that send_medication_reminder was not called
        service.send_medication_reminder.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_check_medications_error(self, mock_db, mock_bot_app):
        """Test error handling in check_medications"""
        service = SchedulerService(mock_db, mock_bot_app)
        
        # Create a medication with missing data to cause an error
        bad_med = (
            1,                  # id
            12345,              # user_id
            "Bad Med",          # name
            # Missing other fields
        )
        
        # Mock the database's get_all_medications method
        mock_db.get_all_medications.return_value = [bad_med]
        
        # Call the method
        await service.check_medications()
        
        # Verify that the error was logged
        mock_bot_app.logger.error.assert_called_once()
        args, kwargs = mock_bot_app.logger.error.call_args
        assert "Ошибка при проверке лекарства" in args[0]
    
    @pytest.mark.asyncio
    async def test_send_medication_reminder(self, mock_db, mock_bot_app):
        """Test sending medication reminder"""
        service = SchedulerService(mock_db, mock_bot_app)
        
        # Call the method
        await service.send_medication_reminder(12345, "Test Med", 2)
        
        # Verify that the bot's send_message method was called with the correct arguments
        mock_bot_app.bot.send_message.assert_called_once()
        args, kwargs = mock_bot_app.bot.send_message.call_args
        
        assert kwargs['chat_id'] == 12345
        assert "Test Med" in kwargs['text']
        assert "2" in kwargs['text']
    
    @pytest.mark.asyncio
    async def test_send_medication_reminder_error(self, mock_db, mock_bot_app):
        """Test error handling in send_medication_reminder"""
        service = SchedulerService(mock_db, mock_bot_app)
        
        # Mock the bot's send_message method to raise an exception
        mock_bot_app.bot.send_message.side_effect = Exception("Test error")
        
        # Call the method
        await service.send_medication_reminder(12345, "Test Med", 2)
        
        # Verify that the error was logged
        mock_bot_app.logger.error.assert_called_once()
        args, kwargs = mock_bot_app.logger.error.call_args
        assert "Ошибка отправки напоминания" in args[0]
