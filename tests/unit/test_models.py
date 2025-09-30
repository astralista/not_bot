import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
from src.bot.models.medication import Medication
from src.bot.models.user import User


class TestMedicationModel:
    """Tests for the Medication model"""
    
    def test_init(self):
        """Test initialization of Medication object"""
        med = Medication(
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
        
        assert med.id == 1
        assert med.user_id == 12345
        assert med.name == "Test Medication"
        assert med.dose_per_intake == 2
        assert med.intakes_per_day == 3
        assert med.start_date == "2025-01-01"
        assert med.duration_value == 10
        assert med.duration_unit == "days"
        assert med.break_value == 5
        assert med.break_unit == "days"
        assert med.cycles == 2
    
    def test_init_defaults(self):
        """Test initialization with default values"""
        med = Medication()
        
        assert med.id is None
        assert med.user_id is None
        assert med.name is None
        assert med.dose_per_intake is None
        assert med.intakes_per_day is None
        assert med.start_date is None
        assert med.duration_value is None
        assert med.duration_unit is None
        assert med.break_value is None
        assert med.break_unit is None
        assert med.cycles == 1  # Default value
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        med = Medication(
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
        
        med_dict = med.to_dict()
        
        assert med_dict["id"] == 1
        assert med_dict["user_id"] == 12345
        assert med_dict["name"] == "Test Medication"
        assert med_dict["dose_per_intake"] == 2
        assert med_dict["intakes_per_day"] == 3
        assert med_dict["start_date"] == "2025-01-01"
        assert med_dict["duration_value"] == 10
        assert med_dict["duration_unit"] == "days"
        assert med_dict["break_value"] == 5
        assert med_dict["break_unit"] == "days"
        assert med_dict["cycles"] == 2
    
    def test_from_dict(self):
        """Test creation from dictionary"""
        med_dict = {
            "id": 1,
            "user_id": 12345,
            "name": "Test Medication",
            "dose_per_intake": 2,
            "intakes_per_day": 3,
            "start_date": "2025-01-01",
            "duration_value": 10,
            "duration_unit": "days",
            "break_value": 5,
            "break_unit": "days",
            "cycles": 2
        }
        
        med = Medication.from_dict(med_dict)
        
        assert med.id == 1
        assert med.user_id == 12345
        assert med.name == "Test Medication"
        assert med.dose_per_intake == 2
        assert med.intakes_per_day == 3
        assert med.start_date == "2025-01-01"
        assert med.duration_value == 10
        assert med.duration_unit == "days"
        assert med.break_value == 5
        assert med.break_unit == "days"
        assert med.cycles == 2
    
    def test_from_dict_missing_fields(self):
        """Test creation from dictionary with missing fields"""
        med_dict = {
            "id": 1,
            "user_id": 12345,
            "name": "Test Medication"
            # Missing other fields
        }
        
        med = Medication.from_dict(med_dict)
        
        assert med.id == 1
        assert med.user_id == 12345
        assert med.name == "Test Medication"
        assert med.dose_per_intake is None
        assert med.intakes_per_day is None
        assert med.start_date is None
        assert med.duration_value is None
        assert med.duration_unit is None
        assert med.break_value is None
        assert med.break_unit is None
        assert med.cycles == 1  # Default value
    
    def test_from_tuple(self):
        """Test creation from tuple"""
        med_tuple = (
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
        
        med = Medication.from_tuple(med_tuple)
        
        assert med.id == 1
        assert med.user_id == 12345
        assert med.name == "Test Medication"
        assert med.dose_per_intake == 2
        assert med.intakes_per_day == 3
        assert med.start_date == "2025-01-01"
        assert med.duration_value == 10
        assert med.duration_unit == "days"
        assert med.break_value == 5
        assert med.break_unit == "days"
        assert med.cycles == 2
    
    def test_from_tuple_without_cycles(self):
        """Test creation from tuple without cycles field"""
        med_tuple = (
            1,                  # id
            12345,              # user_id
            "Test Medication",  # name
            2,                  # dose_per_intake
            3,                  # intakes_per_day
            "2025-01-01",       # start_date
            10,                 # duration_value
            "days",             # duration_unit
            5,                  # break_value
            "days"              # break_unit
            # No cycles
        )
        
        med = Medication.from_tuple(med_tuple)
        
        assert med.id == 1
        assert med.user_id == 12345
        assert med.name == "Test Medication"
        assert med.dose_per_intake == 2
        assert med.intakes_per_day == 3
        assert med.start_date == "2025-01-01"
        assert med.duration_value == 10
        assert med.duration_unit == "days"
        assert med.break_value == 5
        assert med.break_unit == "days"
        assert med.cycles == 1  # Default value
    
    @freeze_time("2025-01-05")
    def test_get_days_left(self):
        """Test calculation of days left"""
        # Test with days as duration unit
        med = Medication(
            start_date="2025-01-01",
            duration_value=10,
            duration_unit="days"
        )
        
        assert med.get_days_left() == 6  # 10 days from Jan 1 - 4 days passed = 6 days left
        
        # Test with months as duration unit
        med = Medication(
            start_date="2025-01-01",
            duration_value=1,
            duration_unit="months"
        )
        
        assert med.get_days_left() == 26  # 30 days from Jan 1 - 4 days passed = 26 days left
    
    def test_get_days_left_no_start_date(self):
        """Test get_days_left with no start date"""
        med = Medication(
            duration_value=10,
            duration_unit="days"
        )
        
        assert med.get_days_left() == 0
    
    @freeze_time("2025-01-05")
    def test_get_next_cycle_date(self):
        """Test calculation of next cycle date"""
        # Test with days as units
        med = Medication(
            start_date="2025-01-01",
            duration_value=10,
            duration_unit="days",
            break_value=5,
            break_unit="days"
        )
        
        next_cycle = med.get_next_cycle_date()
        assert next_cycle.year == 2025
        assert next_cycle.month == 1
        assert next_cycle.day == 16  # Jan 1 + 10 days duration + 5 days break = Jan 16
        
        # Test with months as units
        med = Medication(
            start_date="2025-01-01",
            duration_value=1,
            duration_unit="months",
            break_value=1,
            break_unit="months"
        )
        
        next_cycle = med.get_next_cycle_date()
        assert next_cycle.year == 2025
        assert next_cycle.month == 3
        assert next_cycle.day == 2  # Jan 1 + 30 days + 30 days = Mar 2
    
    def test_get_next_cycle_date_no_start_date(self):
        """Test get_next_cycle_date with no start date"""
        med = Medication(
            duration_value=10,
            duration_unit="days",
            break_value=5,
            break_unit="days"
        )
        
        assert med.get_next_cycle_date() is None


class TestUserModel:
    """Tests for the User model"""
    
    def test_init(self):
        """Test initialization of User object"""
        user = User(user_id=12345, zodiac_sign="овен")
        
        assert user.user_id == 12345
        assert user.zodiac_sign == "овен"
    
    def test_init_defaults(self):
        """Test initialization with default values"""
        user = User(user_id=12345)
        
        assert user.user_id == 12345
        assert user.zodiac_sign is None
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        user = User(user_id=12345, zodiac_sign="овен")
        user_dict = user.to_dict()
        
        assert user_dict["user_id"] == 12345
        assert user_dict["zodiac_sign"] == "овен"
    
    def test_from_dict(self):
        """Test creation from dictionary"""
        user_dict = {
            "user_id": 12345,
            "zodiac_sign": "овен"
        }
        
        user = User.from_dict(user_dict)
        
        assert user.user_id == 12345
        assert user.zodiac_sign == "овен"
    
    def test_from_dict_missing_fields(self):
        """Test creation from dictionary with missing fields"""
        user_dict = {
            "user_id": 12345
            # Missing zodiac_sign
        }
        
        user = User.from_dict(user_dict)
        
        assert user.user_id == 12345
        assert user.zodiac_sign is None
