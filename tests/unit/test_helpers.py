import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time

from src.utils.helpers import calculate_next_notification, format_medication_info


class TestHelpers:
    """Tests for helper functions"""
    
    @freeze_time("2025-01-15 10:00:00")
    def test_calculate_next_notification_one_intake(self):
        """Test calculate_next_notification with one intake per day"""
        # Set up test data
        start_date = datetime(2025, 1, 1).date()
        intakes_per_day = 1
        
        # Call the function
        result = calculate_next_notification(start_date, intakes_per_day)
        
        # Check the result
        assert len(result) == 1
        assert result[0].hour == 9
        assert result[0].minute == 0
        assert result[0].year == 2025
        assert result[0].month == 1
        assert result[0].day == 15  # Today's date from freeze_time
    
    @freeze_time("2025-01-15 10:00:00")
    def test_calculate_next_notification_two_intakes(self):
        """Test calculate_next_notification with two intakes per day"""
        # Set up test data
        start_date = datetime(2025, 1, 1).date()
        intakes_per_day = 2
        
        # Call the function
        result = calculate_next_notification(start_date, intakes_per_day)
        
        # Check the result
        assert len(result) == 2
        assert result[0].hour == 9
        assert result[0].minute == 0
        assert result[1].hour == 21
        assert result[1].minute == 0
    
    @freeze_time("2025-01-15 10:00:00")
    def test_calculate_next_notification_three_intakes(self):
        """Test calculate_next_notification with three intakes per day"""
        # Set up test data
        start_date = datetime(2025, 1, 1).date()
        intakes_per_day = 3
        
        # Call the function
        result = calculate_next_notification(start_date, intakes_per_day)
        
        # Check the result
        assert len(result) == 3
        assert result[0].hour == 9
        assert result[0].minute == 0
        assert result[1].hour == 15
        assert result[1].minute == 0
        assert result[2].hour == 21
        assert result[2].minute == 0
    
    @freeze_time("2025-01-15 10:00:00")
    def test_calculate_next_notification_four_intakes(self):
        """Test calculate_next_notification with four intakes per day"""
        # Set up test data
        start_date = datetime(2025, 1, 1).date()
        intakes_per_day = 4
        
        # Call the function
        result = calculate_next_notification(start_date, intakes_per_day)
        
        # Check the result
        assert len(result) == 4
        assert result[0].hour == 8
        assert result[0].minute == 0
        assert result[1].hour == 11
        assert result[1].minute == 0
        assert result[2].hour == 14
        assert result[2].minute == 0
        assert result[3].hour == 17
        assert result[3].minute == 0
    
    @freeze_time("2025-01-15 10:00:00")
    def test_calculate_next_notification_six_intakes(self):
        """Test calculate_next_notification with six intakes per day"""
        # Set up test data
        start_date = datetime(2025, 1, 1).date()
        intakes_per_day = 6
        
        # Call the function
        result = calculate_next_notification(start_date, intakes_per_day)
        
        # Check the result
        assert len(result) == 6
        assert result[0].hour == 8
        assert result[0].minute == 0
        assert result[1].hour == 10
        assert result[1].minute == 0
        assert result[2].hour == 12
        assert result[2].minute == 0
        assert result[3].hour == 14
        assert result[3].minute == 0
        assert result[4].hour == 16
        assert result[4].minute == 0
        assert result[5].hour == 18
        assert result[5].minute == 0
    
    @freeze_time("2025-01-15 10:00:00")
    def test_format_medication_info_active(self):
        """Test format_medication_info with active medication"""
        # Set up test data - medication with days left
        medication = (
            1,                  # med_id
            12345,              # user_id
            "Аспирин",          # name
            2,                  # dose
            3,                  # intakes
            "2025-01-01",       # start_date
            30,                 # duration_val
            "days",             # duration_unit
            5,                  # break_val
            "days",             # break_unit
            2                   # cycles
        )
        
        # Call the function
        result = format_medication_info(medication)
        
        # Check the result
        assert "Аспирин" in result
        assert "ID: 1" in result
        assert "2 капс. × 3 р/день" in result
        assert "Начало: 2025-01-01" in result
        assert "⏳ Осталось: 16 дней" in result  # 15 Jan to 31 Jan = 16 days
    
    @freeze_time("2025-02-15 10:00:00")
    def test_format_medication_info_break(self):
        """Test format_medication_info with medication on break"""
        # Set up test data - medication on break
        medication = (
            1,                  # med_id
            12345,              # user_id
            "Аспирин",          # name
            2,                  # dose
            3,                  # intakes
            "2025-01-01",       # start_date
            30,                 # duration_val
            "days",             # duration_unit
            10,                 # break_val
            "days",             # break_unit
            2                   # cycles
        )
        
        # Call the function
        result = format_medication_info(medication)
        
        # Check the result
        assert "Аспирин" in result
        assert "ID: 1" in result
        assert "2 капс. × 3 р/день" in result
        assert "Начало: 2025-01-01" in result
        assert "⏸️ Перерыв до 10.02.2025" in result  # 31 Jan + 10 days = 10 Feb
    
    @freeze_time("2025-01-15 10:00:00")
    def test_format_medication_info_months_duration(self):
        """Test format_medication_info with duration in months"""
        # Set up test data - medication with duration in months
        medication = (
            1,                  # med_id
            12345,              # user_id
            "Аспирин",          # name
            2,                  # dose
            3,                  # intakes
            "2025-01-01",       # start_date
            2,                  # duration_val
            "months",           # duration_unit
            1,                  # break_val
            "months",           # break_unit
            2                   # cycles
        )
        
        # Call the function
        result = format_medication_info(medication)
        
        # Check the result
        assert "Аспирин" in result
        assert "ID: 1" in result
        assert "2 капс. × 3 р/день" in result
        assert "Начало: 2025-01-01" in result
        assert "⏳ Осталось: " in result
        
        # 2 months = 60 days, 1 Jan + 60 days = 2 Mar
        # 15 Jan to 2 Mar = 46 days
        assert "⏳ Осталось: 46 дней" in result
