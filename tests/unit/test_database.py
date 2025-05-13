import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from src.core.database import Database


class TestDatabase:
    """Tests for the Database class"""
    
    def test_init(self):
        """Test initialization of Database object"""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            
            db = Database("test.db")
            
            mock_connect.assert_called_once_with("test.db")
            assert db.conn == mock_conn
            
            # Verify that create_table and create_user_settings_table were called
            assert mock_conn.execute.call_count >= 2
            assert mock_conn.commit.call_count >= 2
    
    def test_create_connection_success(self):
        """Test successful database connection creation"""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            
            db = Database(":memory:")
            conn = db.create_connection(":memory:")
            
            mock_connect.assert_called_with(":memory:")
            assert conn == mock_conn
    
    def test_create_connection_failure(self):
        """Test database connection creation failure"""
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.Error("Connection error")
            
            with patch('builtins.print') as mock_print:
                db = Database(":memory:")
                conn = db.create_connection("test.db")
                
                mock_connect.assert_called_with("test.db")
                mock_print.assert_called_once()
                assert conn is None
    
    def test_create_table(self, in_memory_db):
        """Test medications table creation"""
        # Table should already be created in the fixture
        cursor = in_memory_db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='medications'")
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == "medications"
        
        # Check table structure
        cursor.execute("PRAGMA table_info(medications)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        expected_columns = [
            "id", "user_id", "name", "dose_per_intake", "intakes_per_day",
            "start_date", "duration_value", "duration_unit", "break_value",
            "break_unit", "cycles"
        ]
        
        for col in expected_columns:
            assert col in column_names
    
    def test_create_user_settings_table(self, in_memory_db):
        """Test user_settings table creation"""
        # Table should already be created in the fixture
        cursor = in_memory_db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'")
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == "user_settings"
        
        # Check table structure
        cursor.execute("PRAGMA table_info(user_settings)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        expected_columns = ["user_id", "zodiac_sign"]
        
        for col in expected_columns:
            assert col in column_names
    
    def test_add_medication(self, in_memory_db):
        """Test adding a medication"""
        in_memory_db.add_medication(
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
        
        cursor = in_memory_db.conn.cursor()
        cursor.execute("SELECT * FROM medications WHERE user_id=?", (12345,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[1] == 12345  # user_id
        assert result[2] == "Test Medication"  # name
        assert result[3] == 2  # dose_per_intake
        assert result[4] == 3  # intakes_per_day
        assert result[5] == "2025-01-01"  # start_date
        assert result[6] == 10  # duration_value
        assert result[7] == "days"  # duration_unit
        assert result[8] == 5  # break_value
        assert result[9] == "days"  # break_unit
        assert result[10] == 2  # cycles
    
    def test_get_medications(self, in_memory_db):
        """Test getting medications for a user"""
        # Add two medications for the same user
        in_memory_db.add_medication(
            user_id=12345,
            name="Test Medication 1",
            dose_per_intake=2,
            intakes_per_day=3,
            start_date="2025-01-01",
            duration_value=10,
            duration_unit="days",
            break_value=5,
            break_unit="days",
            cycles=2
        )
        
        in_memory_db.add_medication(
            user_id=12345,
            name="Test Medication 2",
            dose_per_intake=1,
            intakes_per_day=2,
            start_date="2025-02-01",
            duration_value=20,
            duration_unit="days",
            break_value=10,
            break_unit="days",
            cycles=1
        )
        
        # Add a medication for a different user
        in_memory_db.add_medication(
            user_id=67890,
            name="Other User Med",
            dose_per_intake=3,
            intakes_per_day=1,
            start_date="2025-03-01",
            duration_value=30,
            duration_unit="days",
            break_value=15,
            break_unit="days",
            cycles=3
        )
        
        # Get medications for the first user
        meds = in_memory_db.get_medications(12345)
        
        assert len(meds) == 2
        assert meds[0][2] == "Test Medication 1"
        assert meds[1][2] == "Test Medication 2"
        
        # Get medications for the second user
        meds = in_memory_db.get_medications(67890)
        
        assert len(meds) == 1
        assert meds[0][2] == "Other User Med"
        
        # Get medications for a non-existent user
        meds = in_memory_db.get_medications(99999)
        
        assert len(meds) == 0
    
    def test_get_medication_by_id(self, in_memory_db):
        """Test getting a medication by ID"""
        # Add a medication
        in_memory_db.add_medication(
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
        
        # Get the medication ID
        cursor = in_memory_db.conn.cursor()
        cursor.execute("SELECT id FROM medications WHERE user_id=?", (12345,))
        med_id = cursor.fetchone()[0]
        
        # Get the medication by ID
        med = in_memory_db.get_medication_by_id(med_id)
        
        assert med is not None
        assert med[0] == med_id
        assert med[1] == 12345
        assert med[2] == "Test Medication"
        
        # Try to get a non-existent medication
        med = in_memory_db.get_medication_by_id(99999)
        
        assert med is None
    
    def test_update_medication(self, in_memory_db):
        """Test updating a medication"""
        # Add a medication
        in_memory_db.add_medication(
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
        
        # Get the medication ID
        cursor = in_memory_db.conn.cursor()
        cursor.execute("SELECT id FROM medications WHERE user_id=?", (12345,))
        med_id = cursor.fetchone()[0]
        
        # Update the medication
        in_memory_db.update_medication(
            med_id,
            name="Updated Medication",
            dose_per_intake=3,
            intakes_per_day=2
        )
        
        # Get the updated medication
        med = in_memory_db.get_medication_by_id(med_id)
        
        assert med is not None
        assert med[2] == "Updated Medication"  # name
        assert med[3] == 3  # dose_per_intake
        assert med[4] == 2  # intakes_per_day
        assert med[5] == "2025-01-01"  # start_date (unchanged)
    
    def test_update_medication_invalid_field(self, in_memory_db):
        """Test updating a medication with an invalid field"""
        # Add a medication
        in_memory_db.add_medication(
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
        
        # Get the medication ID
        cursor = in_memory_db.conn.cursor()
        cursor.execute("SELECT id FROM medications WHERE user_id=?", (12345,))
        med_id = cursor.fetchone()[0]
        
        # Try to update with an invalid field
        with pytest.raises(ValueError):
            in_memory_db.update_medication(
                med_id,
                invalid_field="Invalid"
            )
    
    def test_update_medication_no_data(self, in_memory_db):
        """Test updating a medication with no data"""
        # Add a medication
        in_memory_db.add_medication(
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
        
        # Get the medication ID
        cursor = in_memory_db.conn.cursor()
        cursor.execute("SELECT id FROM medications WHERE user_id=?", (12345,))
        med_id = cursor.fetchone()[0]
        
        # Try to update with no data
        with pytest.raises(ValueError):
            in_memory_db.update_medication(med_id)
    
    def test_update_medication_not_found(self, in_memory_db):
        """Test updating a non-existent medication"""
        with pytest.raises(ValueError):
            in_memory_db.update_medication(
                99999,
                name="Updated Medication"
            )
    
    def test_delete_medication(self, in_memory_db):
        """Test deleting a medication"""
        # Add a medication
        in_memory_db.add_medication(
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
        
        # Get the medication ID
        cursor = in_memory_db.conn.cursor()
        cursor.execute("SELECT id FROM medications WHERE user_id=?", (12345,))
        med_id = cursor.fetchone()[0]
        
        # Delete the medication
        in_memory_db.delete_medication(med_id)
        
        # Try to get the deleted medication
        med = in_memory_db.get_medication_by_id(med_id)
        
        assert med is None
    
    def test_get_all_medications(self, in_memory_db):
        """Test getting all medications"""
        # Add medications for different users
        in_memory_db.add_medication(
            user_id=12345,
            name="User 1 Med 1",
            dose_per_intake=2,
            intakes_per_day=3,
            start_date="2025-01-01",
            duration_value=10,
            duration_unit="days",
            break_value=5,
            break_unit="days",
            cycles=2
        )
        
        in_memory_db.add_medication(
            user_id=12345,
            name="User 1 Med 2",
            dose_per_intake=1,
            intakes_per_day=2,
            start_date="2025-02-01",
            duration_value=20,
            duration_unit="days",
            break_value=10,
            break_unit="days",
            cycles=1
        )
        
        in_memory_db.add_medication(
            user_id=67890,
            name="User 2 Med",
            dose_per_intake=3,
            intakes_per_day=1,
            start_date="2025-03-01",
            duration_value=30,
            duration_unit="days",
            break_value=15,
            break_unit="days",
            cycles=3
        )
        
        # Get all medications
        meds = in_memory_db.get_all_medications()
        
        assert len(meds) == 3
        med_names = [med[2] for med in meds]
        assert "User 1 Med 1" in med_names
        assert "User 1 Med 2" in med_names
        assert "User 2 Med" in med_names
    
    def test_get_all_users(self, in_memory_db):
        """Test getting all users"""
        # Add medications for different users
        in_memory_db.add_medication(
            user_id=12345,
            name="User 1 Med",
            dose_per_intake=2,
            intakes_per_day=3,
            start_date="2025-01-01",
            duration_value=10,
            duration_unit="days",
            break_value=5,
            break_unit="days",
            cycles=2
        )
        
        in_memory_db.add_medication(
            user_id=67890,
            name="User 2 Med",
            dose_per_intake=3,
            intakes_per_day=1,
            start_date="2025-03-01",
            duration_value=30,
            duration_unit="days",
            break_value=15,
            break_unit="days",
            cycles=3
        )
        
        # Get all users
        users = in_memory_db.get_all_users()
        
        assert len(users) == 2
        assert 12345 in users
        assert 67890 in users
    
    def test_get_medication_field_names(self, in_memory_db):
        """Test getting medication field names"""
        field_names = in_memory_db.get_medication_field_names()
        
        expected_fields = [
            "id", "user_id", "name", "dose_per_intake", "intakes_per_day",
            "start_date", "duration_value", "duration_unit", "break_value",
            "break_unit", "cycles"
        ]
        
        for field in expected_fields:
            assert field in field_names
    
    def test_add_user_settings(self, in_memory_db):
        """Test adding user settings"""
        in_memory_db.add_user_settings(12345, "овен")
        
        cursor = in_memory_db.conn.cursor()
        cursor.execute("SELECT * FROM user_settings WHERE user_id=?", (12345,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == 12345  # user_id
        assert result[1] == "овен"  # zodiac_sign
    
    def test_update_user_settings(self, in_memory_db):
        """Test updating user settings"""
        # Add initial settings
        in_memory_db.add_user_settings(12345, "овен")
        
        # Update settings
        in_memory_db.add_user_settings(12345, "телец")
        
        cursor = in_memory_db.conn.cursor()
        cursor.execute("SELECT * FROM user_settings WHERE user_id=?", (12345,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == 12345  # user_id
        assert result[1] == "телец"  # zodiac_sign
    
    def test_get_user_zodiac(self, in_memory_db):
        """Test getting user zodiac sign"""
        # Add user settings
        in_memory_db.add_user_settings(12345, "овен")
        
        # Get zodiac sign
        zodiac = in_memory_db.get_user_zodiac(12345)
        
        assert zodiac == "овен"
        
        # Get zodiac sign for non-existent user
        zodiac = in_memory_db.get_user_zodiac(99999)
        
        assert zodiac is None
