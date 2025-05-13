import pytest
from datetime import datetime
from src.utils.validators import (
    validate_date,
    validate_number,
    validate_unit,
    validate_zodiac_sign
)


class TestValidateDate:
    """Tests for validate_date function"""
    
    def test_valid_date(self):
        """Test with valid date format"""
        assert validate_date("2025-01-01") is True
        assert validate_date("2023-12-31") is True
        assert validate_date("2024-02-29") is True  # Leap year
    
    def test_invalid_date_format(self):
        """Test with invalid date format"""
        assert validate_date("01-01-2025") is False
        assert validate_date("2025/01/01") is False
        assert validate_date("2025.01.01") is False
        assert validate_date("25-01-01") is False
        assert validate_date("01-Jan-2025") is False
    
    def test_invalid_date_values(self):
        """Test with invalid date values"""
        assert validate_date("2025-13-01") is False  # Invalid month
        assert validate_date("2025-01-32") is False  # Invalid day
        assert validate_date("2023-02-29") is False  # Not a leap year
        assert validate_date("2025-04-31") is False  # April has 30 days
    
    def test_non_date_strings(self):
        """Test with non-date strings"""
        assert validate_date("") is False
        assert validate_date("abc") is False
        assert validate_date("2025-ab-01") is False
        assert validate_date("2025-01-ab") is False


class TestValidateNumber:
    """Tests for validate_number function"""
    
    def test_valid_numbers(self):
        """Test with valid numbers"""
        assert validate_number("1") is True
        assert validate_number("10") is True
        assert validate_number("100") is True
    
    def test_with_min_value(self):
        """Test with minimum value constraint"""
        assert validate_number("5", min_val=5) is True
        assert validate_number("5", min_val=6) is False
        assert validate_number("10", min_val=5) is True
    
    def test_with_max_value(self):
        """Test with maximum value constraint"""
        assert validate_number("5", max_val=10) is True
        assert validate_number("10", max_val=10) is True
        assert validate_number("11", max_val=10) is False
    
    def test_with_min_and_max_value(self):
        """Test with both min and max value constraints"""
        assert validate_number("5", min_val=1, max_val=10) is True
        assert validate_number("1", min_val=1, max_val=10) is True
        assert validate_number("10", min_val=1, max_val=10) is True
        assert validate_number("0", min_val=1, max_val=10) is False
        assert validate_number("11", min_val=1, max_val=10) is False
    
    def test_non_numeric_strings(self):
        """Test with non-numeric strings"""
        assert validate_number("") is False
        assert validate_number("abc") is False
        assert validate_number("1a") is False
        assert validate_number("1.5") is False  # Not an integer
        assert validate_number("-1") is False  # Negative number


class TestValidateUnit:
    """Tests for validate_unit function"""
    
    def test_valid_units(self):
        """Test with valid units"""
        assert validate_unit("days") is True
        assert validate_unit("months") is True
        assert validate_unit("DAYS") is True  # Case insensitive
        assert validate_unit("MONTHS") is True  # Case insensitive
        assert validate_unit("Days") is True  # Mixed case
        assert validate_unit("Months") is True  # Mixed case
    
    def test_invalid_units(self):
        """Test with invalid units"""
        assert validate_unit("") is False
        assert validate_unit("day") is False
        assert validate_unit("month") is False
        assert validate_unit("weeks") is False
        assert validate_unit("years") is False
        assert validate_unit("d") is False
        assert validate_unit("m") is False


class TestValidateZodiacSign:
    """Tests for validate_zodiac_sign function"""
    
    def test_valid_zodiac_signs(self):
        """Test with valid zodiac signs"""
        valid_signs = [
            "овен", "телец", "близнецы", "рак", "лев",
            "дева", "весы", "скорпион", "стрелец",
            "козерог", "водолей", "рыбы"
        ]
        
        for sign in valid_signs:
            assert validate_zodiac_sign(sign) is True
            assert validate_zodiac_sign(sign.upper()) is True  # Case insensitive
            assert validate_zodiac_sign(sign.capitalize()) is True  # Mixed case
    
    def test_invalid_zodiac_signs(self):
        """Test with invalid zodiac signs"""
        assert validate_zodiac_sign("") is False
        assert validate_zodiac_sign("овн") is False  # Typo
        assert validate_zodiac_sign("рыба") is False  # Singular
        assert validate_zodiac_sign("aries") is False  # English
        assert validate_zodiac_sign("123") is False
        assert validate_zodiac_sign("знак") is False
