import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
from src.utils.helpers import calculate_next_notification, format_medication_info


class TestCalculateNextNotification:
    """Tests for calculate_next_notification function"""
    
    @freeze_time("2025-05-13 10:00:00")
    def test_single_intake(self):
        """Test with single intake per day"""
        start_date = datetime(2025, 5, 1).date()
        result = calculate_next_notification(start_date, 1)
        
        assert len(result) == 1
        assert result[0].hour == 9
        assert result[0].minute == 0
        assert result[0].day == datetime.now().day
        assert result[0].month == datetime.now().month
        assert result[0].year == datetime.now().year
    
    @freeze_time("2025-05-13 10:00:00")
    def test_two_intakes(self):
        """Test with two intakes per day"""
        start_date = datetime(2025, 5, 1).date()
        result = calculate_next_notification(start_date, 2)
        
        assert len(result) == 2
        assert result[0].hour == 9
        assert result[0].minute == 0
        assert result[1].hour == 21
        assert result[1].minute == 0
    
    @freeze_time("2025-05-13 10:00:00")
    def test_three_intakes(self):
        """Test with three intakes per day"""
        start_date = datetime(2025, 5, 1).date()
        result = calculate_next_notification(start_date, 3)
        
        assert len(result) == 3
        assert result[0].hour == 9
        assert result[0].minute == 0
        assert result[1].hour == 15
        assert result[1].minute == 0
        assert result[2].hour == 21
        assert result[2].minute == 0
    
    @freeze_time("2025-05-13 10:00:00")
    def test_multiple_intakes(self):
        """Test with more than three intakes per day"""
        start_date = datetime(2025, 5, 1).date()
        result = calculate_next_notification(start_date, 4)
        
        assert len(result) == 4
        # Should be evenly distributed between 8:00 and 22:00
        assert result[0].hour == 8
        assert result[1].hour == 11
        assert result[2].hour == 14
        assert result[3].hour == 17
        
        # Test with 6 intakes
        result = calculate_next_notification(start_date, 6)
        assert len(result) == 6
        assert result[0].hour == 8
        assert result[1].hour == 10
        assert result[2].hour == 12
        assert result[3].hour == 14
        assert result[4].hour == 16
        assert result[5].hour == 18


class TestFormatMedicationInfo:
    """Tests for format_medication_info function"""
    
    @freeze_time("2025-05-13")
    def test_active_medication(self):
        """Test formatting for active medication"""
        # Medication with future end date (active)
        medication = (
            1,                  # id
            12345,              # user_id
            "Test Med",         # name
            2,                  # dose_per_intake
            3,                  # intakes_per_day
            "2025-05-01",       # start_date
            30,                 # duration_value
            "days",             # duration_unit
            5,                  # break_value
            "days",             # break_unit
            2                   # cycles
        )
        
        result = format_medication_info(medication)
        
        assert "Test Med" in result
        assert "ID: 1" in result
        assert "2 капс. × 3 р/день" in result
        assert "Начало: 2025-05-01" in result
        assert "⏳ Осталось: 18 дней" in result  # 13 May to 31 May = 18 days
    
    @freeze_time("2025-06-15")
    def test_on_break_medication(self):
        """Test formatting for medication on break"""
        # Medication with past end date (on break)
        medication = (
            1,                  # id
            12345,              # user_id
            "Test Med",         # name
            2,                  # dose_per_intake
            3,                  # intakes_per_day
            "2025-05-01",       # start_date
            30,                 # duration_value
            "days",             # duration_unit
            10,                 # break_value
            "days",             # break_unit
            2                   # cycles
        )
        
        result = format_medication_info(medication)
        
        assert "Test Med" in result
        assert "ID: 1" in result
        assert "2 капс. × 3 р/день" in result
        assert "Начало: 2025-05-01" in result
        assert "⏸️ Перерыв до 10.06.2025" in result  # 31 May + 10 days = 10 June
    
    @freeze_time("2025-05-13")
    def test_with_months_duration(self):
        """Test formatting with months as duration unit"""
        medication = (
            1,                  # id
            12345,              # user_id
            "Test Med",         # name
            2,                  # dose_per_intake
            3,                  # intakes_per_day
            "2025-05-01",       # start_date
            1,                  # duration_value
            "months",           # duration_unit
            1,                  # break_value
            "months",           # break_unit
            2                   # cycles
        )
        
        result = format_medication_info(medication)
        
        assert "Test Med" in result
        assert "⏳ Осталось: 18 дней" in result  # 13 May to 31 May = 18 days
