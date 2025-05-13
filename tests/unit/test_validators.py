import pytest
from src.utils.validators import validate_date, validate_number, validate_unit, validate_zodiac_sign


class TestValidators:
    """Tests for validator functions"""
    
    def test_validate_date_valid(self):
        """Test validate_date with valid dates"""
        valid_dates = [
            "2025-01-01",
            "2025-12-31",
            "2025-02-28",
            "2024-02-29",  # Leap year
        ]
        
        for date in valid_dates:
            assert validate_date(date) is True
    
    def test_validate_date_invalid_format(self):
        """Test validate_date with invalid format"""
        invalid_formats = [
            "01-01-2025",  # Wrong order
            "2025/01/01",  # Wrong separator
            "2025.01.01",  # Wrong separator
            "25-01-01",    # Incomplete year
            "2025-1-01",   # Missing leading zero
            "2025-01-1",   # Missing leading zero
            "2025-01",     # Missing day
            "01-01",       # Missing year
            "2025-01-01 ",  # Extra space
            " 2025-01-01",  # Extra space
            "",            # Empty string
        ]
        
        for date in invalid_formats:
            assert validate_date(date) is False
    
    def test_validate_date_invalid_values(self):
        """Test validate_date with invalid date values"""
        invalid_values = [
            "2025-00-01",  # Month 0
            "2025-13-01",  # Month 13
            "2025-01-00",  # Day 0
            "2025-01-32",  # Day 32
            "2025-04-31",  # April has 30 days
            "2025-02-29",  # Not a leap year
            "2025-02-30",  # February never has 30 days
        ]
        
        for date in invalid_values:
            assert validate_date(date) is False
    
    def test_validate_number_valid(self):
        """Test validate_number with valid numbers"""
        # Default range (min=1, max=None)
        assert validate_number("1") is True
        assert validate_number("5") is True
        assert validate_number("100") is True
        
        # Custom min
        assert validate_number("5", min_val=5) is True
        assert validate_number("10", min_val=5) is True
        
        # Custom max
        assert validate_number("5", max_val=10) is True
        assert validate_number("10", max_val=10) is True
        
        # Custom range
        assert validate_number("5", min_val=1, max_val=10) is True
        assert validate_number("1", min_val=1, max_val=10) is True
        assert validate_number("10", min_val=1, max_val=10) is True
    
    def test_validate_number_invalid(self):
        """Test validate_number with invalid numbers"""
        # Not a number
        assert validate_number("abc") is False
        assert validate_number("1.5") is False
        assert validate_number("1,5") is False
        assert validate_number("1a") is False
        assert validate_number("") is False
        assert validate_number(" ") is False
        
        # Below min
        assert validate_number("0") is False  # Default min is 1
        assert validate_number("4", min_val=5) is False
        
        # Above max
        assert validate_number("11", max_val=10) is False
        
        # Outside range
        assert validate_number("0", min_val=1, max_val=10) is False
        assert validate_number("11", min_val=1, max_val=10) is False
    
    def test_validate_unit_valid(self):
        """Test validate_unit with valid units"""
        assert validate_unit("days") is True
        assert validate_unit("months") is True
        assert validate_unit("DAYS") is True
        assert validate_unit("MONTHS") is True
        assert validate_unit("Days") is True
        assert validate_unit("Months") is True
    
    def test_validate_unit_invalid(self):
        """Test validate_unit with invalid units"""
        assert validate_unit("day") is False
        assert validate_unit("month") is False
        assert validate_unit("weeks") is False
        assert validate_unit("years") is False
        assert validate_unit("") is False
        assert validate_unit(" days") is False
        assert validate_unit("days ") is False
    
    def test_validate_zodiac_sign_valid(self):
        """Test validate_zodiac_sign with valid signs"""
        valid_signs = [
            "овен", "телец", "близнецы", "рак", "лев",
            "дева", "весы", "скорпион", "стрелец",
            "козерог", "водолей", "рыбы"
        ]
        
        for sign in valid_signs:
            assert validate_zodiac_sign(sign) is True
            assert validate_zodiac_sign(sign.upper()) is True
            assert validate_zodiac_sign(sign.capitalize()) is True
    
    def test_validate_zodiac_sign_invalid(self):
        """Test validate_zodiac_sign with invalid signs"""
        invalid_signs = [
            "овн",  # Typo
            "рыба",  # Singular
            "скорпеон",  # Typo
            "змея",  # Not a zodiac sign
            "dragon",  # English
            "aries",  # English
            "",  # Empty
            " овен",  # Extra space
            "овен ",  # Extra space
        ]
        
        for sign in invalid_signs:
            assert validate_zodiac_sign(sign) is False
