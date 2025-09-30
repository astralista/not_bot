import pytest
import sqlite3
from unittest.mock import patch, MagicMock, call
import os

from src.core.database import Database


class TestDatabase:
    """Tests for the Database class"""
    
    @pytest.fixture
    def mock_logger(self):
        """Fixture for mocking logger"""
        with patch('src.core.database.logger') as mock_logger:
            mock_child_logger = MagicMock()
            mock_logger.getChild.return_value = mock_child_logger
            yield mock_logger
    
    @pytest.fixture
    def mock_sqlite3(self):
        """Fixture for mocking sqlite3"""
        with patch('src.core.database.sqlite3') as mock_sqlite3:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_connection.cursor.return_value = mock_cursor
            mock_sqlite3.connect.return_value = mock_connection
            yield mock_sqlite3, mock_connection, mock_cursor
    
    def test_init(self, mock_logger, mock_sqlite3):
        """Test Database initialization"""
        mock_sqlite3, mock_connection, _ = mock_sqlite3
        
        # Create a database instance
        db = Database("test.db")
        
        # Verify that the connection was created
        mock_sqlite3.connect.assert_called_once_with("test.db")
        
        # Verify that the tables were created
        assert mock_connection.execute.call_count == 2
        assert mock_connection.commit.call_count == 2
        
        # Verify that the logger was initialized
        mock_logger.getChild.assert_called_once_with('Database')
        assert db.logger == mock_logger.getChild.return_value
    
    def test_create_connection_success(self, mock_logger, mock_sqlite3):
        """Test create_connection with successful connection"""
        mock_sqlite3, mock_connection, _ = mock_sqlite3
        
        # Create a database instance
        db = Database("test.db")
        
        # Reset the mock to test create_connection directly
        mock_sqlite3.connect.reset_mock()
        
        # Call create_connection
        result = db.create_connection("test.db")
        
        # Verify that connect was called
        mock_sqlite3.connect.assert_called_once_with("test.db")
        
        # Verify that the connection was returned
        assert result == mock_connection
    
    def test_create_connection_error(self, mock_logger, mock_sqlite3):
        """Test create_connection with error"""
        mock_sqlite3, _, _ = mock_sqlite3
        
        # Mock sqlite3.connect to raise an exception
        mock_sqlite3.connect.side_effect = sqlite3.Error("Connection error")
        
        # Create a database instance with patched print
        with patch('builtins.print') as mock_print:
            db = Database("test.db")
            
            # Reset the mock to test create_connection directly
            mock_sqlite3.connect.reset_mock()
            mock_sqlite3.connect.side_effect = sqlite3.Error("Connection error")
            
            # Call create_connection
            result = db.create_connection("test.db")
            
            # Verify that connect was called
            mock_sqlite3.connect.assert_called_once_with("test.db")
            
            # Verify that the error was printed
            mock_print.assert_called_once()
            
            # Verify that None was returned
            assert result is None
    
    def test_create_table(self, mock_logger, mock_sqlite3):
        """Test create_table method"""
        _, mock_connection, _ = mock_sqlite3
        
        # Create a database instance
        db = Database("test.db")
        
        # Reset the mock to test create_table directly
        mock_connection.execute.reset_mock()
        mock_connection.commit.reset_mock()
        
        # Call create_table
        db.create_table()
        
        # Verify that execute was called with the correct SQL
        mock_connection.execute.assert_called_once()
        args, _ = mock_connection.execute.call_args
        sql = args[0]
        assert "CREATE TABLE IF NOT EXISTS medications" in sql
        
        # Verify that commit was called
        mock_connection.commit.assert_called_once()
    
    def test_create_user_settings_table(self, mock_logger, mock_sqlite3):
        """Test create_user_settings_table method"""
        _, mock_connection, _ = mock_sqlite3
        
        # Create a database instance
        db = Database("test.db")
        
        # Reset the mock to test create_user_settings_table directly
        mock_connection.execute.reset_mock()
        mock_connection.commit.reset_mock()
        
        # Call create_user_settings_table
        db.create_user_settings_table()
        
        # Verify that execute was called with the correct SQL
        mock_connection.execute.assert_called_once()
        args, _ = mock_connection.execute.call_args
        sql = args[0]
        assert "CREATE TABLE IF NOT EXISTS user_settings" in sql
        
        # Verify that commit was called
        mock_connection.commit.assert_called_once()
    
    def test_add_medication(self, mock_logger, mock_sqlite3):
        """Test add_medication method"""
        _, mock_connection, _ = mock_sqlite3
        
        # Create a database instance
        db = Database("test.db")
        
        # Reset the mock to test add_medication directly
        mock_connection.execute.reset_mock()
        mock_connection.commit.reset_mock()
        
        # Call add_medication
        db.add_medication(
            user_id=12345,
            name="Аспирин",
            dose_per_intake=2,
            intakes_per_day=3,
            start_date="2025-01-01",
            duration_value=30,
            duration_unit="days",
            break_value=5,
            break_unit="days",
            cycles=2
        )
        
        # Verify that execute was called with the correct SQL and parameters
        mock_connection.execute.assert_called_once()
        args, kwargs = mock_connection.execute.call_args
        sql = args[0]
        params = args[1]
        
        assert "INSERT INTO medications" in sql
        assert params == (12345, "Аспирин", 2, 3, "2025-01-01", 30, "days", 5, "days", 2)
        
        # Verify that commit was called
        mock_connection.commit.assert_called_once()
    
    def test_get_medications(self, mock_logger, mock_sqlite3):
        """Test get_medications method"""
        _, mock_connection, mock_cursor = mock_sqlite3
        
        # Mock cursor.fetchall to return medications
        mock_medications = [
            (1, 12345, "Аспирин", 2, 3, "2025-01-01", 30, "days", 5, "days", 2),
            (2, 12345, "Витамин C", 1, 1, "2025-02-01", 60, "days", 0, "days", 1)
        ]
        mock_cursor.fetchall.return_value = mock_medications
        
        # Create a database instance
        db = Database("test.db")
        
        # Reset the mocks to test get_medications directly
        mock_connection.cursor.reset_mock()
        mock_cursor.execute.reset_mock()
        mock_cursor.fetchall.reset_mock()
        
        # Call get_medications
        result = db.get_medications(12345)
        
        # Verify that cursor was created
        mock_connection.cursor.assert_called_once()
        
        # Verify that execute was called with the correct SQL and parameters
        mock_cursor.execute.assert_called_once()
        args, kwargs = mock_cursor.execute.call_args
        sql = args[0]
        params = args[1]
        
        assert "SELECT * FROM medications WHERE user_id=?" in sql
        assert params == (12345,)
        
        # Verify that fetchall was called
        mock_cursor.fetchall.assert_called_once()
        
        # Verify that the medications were returned
        assert result == mock_medications
    
    def test_get_medication_by_id(self, mock_logger, mock_sqlite3):
        """Test get_medication_by_id method"""
        _, mock_connection, mock_cursor = mock_sqlite3
        
        # Mock cursor.fetchone to return a medication
        mock_medication = (1, 12345, "Аспирин", 2, 3, "2025-01-01", 30, "days", 5, "days", 2)
        mock_cursor.fetchone.return_value = mock_medication
        
        # Create a database instance
        db = Database("test.db")
        
        # Reset the mocks to test get_medication_by_id directly
        mock_connection.cursor.reset_mock()
        mock_cursor.execute.reset_mock()
        mock_cursor.fetchone.reset_mock()
        
        # Call get_medication_by_id
        result = db.get_medication_by_id(1)
        
        # Verify that cursor was created
        mock_connection.cursor.assert_called_once()
        
        # Verify that execute was called with the correct SQL and parameters
        mock_cursor.execute.assert_called_once()
        args, kwargs = mock_cursor.execute.call_args
        sql = args[0]
        params = args[1]
        
        assert "SELECT * FROM medications WHERE id=?" in sql
        assert params == (1,)
        
        # Verify that fetchone was called
        mock_cursor.fetchone.assert_called_once()
        
        # Verify that the medication was returned
        assert result == mock_medication
    
    def test_update_medication_success(self, mock_logger, mock_sqlite3):
        """Test update_medication method with successful update"""
        _, mock_connection, mock_cursor = mock_sqlite3
        
        # Mock cursor.rowcount to indicate a successful update
        mock_cursor.rowcount = 1
        mock_connection.cursor.return_value = mock_cursor
        
        # Create a database instance
        db = Database("test.db")
        
        # Mock get_medication_field_names to return allowed fields
        db.get_medication_field_names = MagicMock(return_value=[
            "id", "user_id", "name", "dose_per_intake", "intakes_per_day",
            "start_date", "duration_value", "duration_unit", "break_value", "break_unit", "cycles"
        ])
        
        # Reset the mocks to test update_medication directly
        mock_connection.cursor.reset_mock()
        mock_cursor.execute.reset_mock()
        mock_connection.commit.reset_mock()
        
        # Call update_medication
        db.update_medication(
            med_id=1,
            name="Новый Аспирин",
            dose_per_intake=3
        )
        
        # Verify that cursor was created
        mock_connection.cursor.assert_called_once()
        
        # Verify that execute was called with the correct SQL and parameters
        mock_cursor.execute.assert_called_once()
        args, kwargs = mock_cursor.execute.call_args
        sql = args[0]
        params = args[1]
        
        assert "UPDATE medications SET" in sql
        assert "name = ?" in sql
        assert "dose_per_intake = ?" in sql
        assert "WHERE id = ?" in sql
        assert params == ["Новый Аспирин", 3, 1]
        
        # Verify that commit was called
        mock_connection.commit.assert_called_once()
    
    def test_update_medication_no_data(self, mock_logger, mock_sqlite3):
        """Test update_medication with no data"""
        _, mock_connection, _ = mock_sqlite3
        
        # Create a database instance
        db = Database("test.db")
        
        # Call update_medication with no data
        with pytest.raises(ValueError) as excinfo:
            db.update_medication(med_id=1)
        
        # Verify that the correct error was raised
        assert "Нет данных для обновления" in str(excinfo.value)
        
        # Verify that execute was not called
        mock_connection.execute.assert_not_called()
    
    def test_update_medication_invalid_field(self, mock_logger, mock_sqlite3):
        """Test update_medication with invalid field"""
        _, mock_connection, _ = mock_sqlite3
        
        # Create a database instance
        db = Database("test.db")
        
        # Mock get_medication_field_names to return allowed fields
        db.get_medication_field_names = MagicMock(return_value=[
            "id", "user_id", "name", "dose_per_intake", "intakes_per_day"
        ])
        
        # Call update_medication with invalid field
        with pytest.raises(ValueError) as excinfo:
            db.update_medication(med_id=1, invalid_field="value")
        
        # Verify that the correct error was raised
        assert "Недопустимое поле: invalid_field" in str(excinfo.value)
        
        # Verify that execute was not called
        mock_connection.execute.assert_not_called()
    
    def test_update_medication_not_found(self, mock_logger, mock_sqlite3):
        """Test update_medication with medication not found"""
        _, mock_connection, mock_cursor = mock_sqlite3
        
        # Mock cursor.rowcount to indicate no rows updated
        mock_cursor.rowcount = 0
        mock_connection.cursor.return_value = mock_cursor
        
        # Create a database instance
        db = Database("test.db")
        
        # Mock get_medication_field_names to return allowed fields
        db.get_medication_field_names = MagicMock(return_value=[
            "id", "user_id", "name", "dose_per_intake", "intakes_per_day"
        ])
        
        # Reset the mocks to test update_medication directly
        mock_connection.cursor.reset_mock()
        mock_cursor.execute.reset_mock()
        
        # Call update_medication
        with pytest.raises(ValueError) as excinfo:
            db.update_medication(med_id=999, name="Новый Аспирин")
        
        # Verify that the correct error was raised
        assert "Запись не найдена или данные не изменились" in str(excinfo.value)
        
        # Verify that rollback was called
        mock_connection.rollback.assert_not_called()  # No rollback needed for this error
    
    def test_update_medication_db_error(self, mock_logger, mock_sqlite3):
        """Test update_medication with database error"""
        _, mock_connection, mock_cursor = mock_sqlite3
        
        # Mock cursor.execute to raise an exception
        mock_cursor.execute.side_effect = sqlite3.Error("Database error")
        mock_connection.cursor.return_value = mock_cursor
        
        # Create a database instance
        db = Database("test.db")
        
        # Mock get_medication_field_names to return allowed fields
        db.get_medication_field_names = MagicMock(return_value=[
            "id", "user_id", "name", "dose_per_intake", "intakes_per_day"
        ])
        
        # Reset the mocks to test update_medication directly
        mock_connection.cursor.reset_mock()
        mock_cursor.execute.reset_mock()
        mock_connection.rollback.reset_mock()
        
        # Call update_medication
        with pytest.raises(Exception) as excinfo:
            db.update_medication(med_id=1, name="Новый Аспирин")
        
        # Verify that the correct error was raised
        assert "Ошибка базы данных: Database error" in str(excinfo.value)
        
        # Verify that rollback was called
        mock_connection.rollback.assert_called_once()
    
    def test_delete_medication(self, mock_logger, mock_sqlite3):
        """Test delete_medication method"""
        _, mock_connection, _ = mock_sqlite3
        
        # Create a database instance
        db = Database("test.db")
        
        # Reset the mock to test delete_medication directly
        mock_connection.execute.reset_mock()
        mock_connection.commit.reset_mock()
        
        # Call delete_medication
        db.delete_medication(1)
        
        # Verify that execute was called with the correct SQL and parameters
        mock_connection.execute.assert_called_once()
        args, kwargs = mock_connection.execute.call_args
        sql = args[0]
        params = args[1]
        
        assert "DELETE FROM medications WHERE id=?" in sql
        assert params == (1,)
        
        # Verify that commit was called
        mock_connection.commit.assert_called_once()
    
    def test_get_all_medications(self, mock_logger, mock_sqlite3):
        """Test get_all_medications method"""
        _, mock_connection, mock_cursor = mock_sqlite3
        
        # Mock cursor.fetchall to return medications
        mock_medications = [
            (1, 12345, "Аспирин", 2, 3, "2025-01-01", 30, "days", 5, "days", 2),
            (2, 67890, "Витамин C", 1, 1, "2025-02-01", 60, "days", 0, "days", 1)
        ]
        mock_cursor.fetchall.return_value = mock_medications
        
        # Create a database instance
        db = Database("test.db")
        
        # Reset the mocks to test get_all_medications directly
        mock_connection.cursor.reset_mock()
        mock_cursor.execute.reset_mock()
        mock_cursor.fetchall.reset_mock()
        
        # Call get_all_medications
        result = db.get_all_medications()
        
        # Verify that cursor was created
        mock_connection.cursor.assert_called_once()
        
        # Verify that execute was called with the correct SQL
        mock_cursor.execute.assert_called_once()
        args, kwargs = mock_cursor.execute.call_args
        sql = args[0]
        
        assert "SELECT * FROM medications" in sql
        
        # Verify that fetchall was called
        mock_cursor.fetchall.assert_called_once()
        
        # Verify that the medications were returned
        assert result == mock_medications
    
    def test_get_all_users(self, mock_logger, mock_sqlite3):
        """Test get_all_users method"""
        _, mock_connection, mock_cursor = mock_sqlite3
        
        # Mock cursor.fetchall to return user IDs
        mock_cursor.fetchall.return_value = [(12345,), (67890,)]
        
        # Create a database instance
        db = Database("test.db")
        
        # Reset the mocks to test get_all_users directly
        mock_connection.cursor.reset_mock()
        mock_cursor.execute.reset_mock()
        mock_cursor.fetchall.reset_mock()
        
        # Call get_all_users
        result = db.get_all_users()
        
        # Verify that cursor was created
        mock_connection.cursor.assert_called_once()
        
        # Verify that execute was called with the correct SQL
        mock_cursor.execute.assert_called_once()
        args, kwargs = mock_cursor.execute.call_args
        sql = args[0]
        
        assert "SELECT DISTINCT user_id FROM medications" in sql
        
        # Verify that fetchall was called
        mock_cursor.fetchall.assert_called_once()
        
        # Verify that the user IDs were returned
        assert result == [12345, 67890]
    
    def test_get_medication_field_names(self, mock_logger, mock_sqlite3):
        """Test get_medication_field_names method"""
        _, mock_connection, mock_cursor = mock_sqlite3
        
        # Mock cursor.fetchall to return field names
        mock_cursor.fetchall.return_value = [
            (0, "id", "INTEGER", 0, None, 1),
            (1, "user_id", "INTEGER", 1, None, 0),
            (2, "name", "TEXT", 1, None, 0)
        ]
        
        # Create a database instance
        db = Database("test.db")
        
        # Reset the mocks to test get_medication_field_names directly
        mock_connection.cursor.reset_mock()
        mock_cursor.execute.reset_mock()
        mock_cursor.fetchall.reset_mock()
        
        # Call get_medication_field_names
        result = db.get_medication_field_names()
        
        # Verify that cursor was created
        mock_connection.cursor.assert_called_once()
        
        # Verify that execute was called with the correct SQL
        mock_cursor.execute.assert_called_once()
        args, kwargs = mock_cursor.execute.call_args
        sql = args[0]
        
        assert "PRAGMA table_info(medications)" in sql
        
        # Verify that fetchall was called
        mock_cursor.fetchall.assert_called_once()
        
        # Verify that the field names were returned
        assert result == ["id", "user_id", "name"]
    
    def test_add_user_settings(self, mock_logger, mock_sqlite3):
        """Test add_user_settings method"""
        _, mock_connection, _ = mock_sqlite3
        
        # Create a database instance
        db = Database("test.db")
        
        # Reset the mock to test add_user_settings directly
        mock_connection.execute.reset_mock()
        mock_connection.commit.reset_mock()
        
        # Call add_user_settings
        db.add_user_settings(12345, "овен")
        
        # Verify that execute was called with the correct SQL and parameters
        mock_connection.execute.assert_called_once()
        args, kwargs = mock_connection.execute.call_args
        sql = args[0]
        params = args[1]
        
        assert "INSERT OR REPLACE INTO user_settings" in sql
        assert params == (12345, "овен")
        
        # Verify that commit was called
        mock_connection.commit.assert_called_once()
    
    def test_get_user_zodiac_exists(self, mock_logger, mock_sqlite3):
        """Test get_user_zodiac method with existing zodiac sign"""
        _, mock_connection, mock_cursor = mock_sqlite3
        
        # Mock cursor.fetchone to return a zodiac sign
        mock_cursor.fetchone.return_value = ("овен",)
        
        # Create a database instance
        db = Database("test.db")
        
        # Reset the mocks to test get_user_zodiac directly
        mock_connection.cursor.reset_mock()
        mock_cursor.execute.reset_mock()
        mock_cursor.fetchone.reset_mock()
        
        # Call get_user_zodiac
        result = db.get_user_zodiac(12345)
        
        # Verify that cursor was created
        mock_connection.cursor.assert_called_once()
        
        # Verify that execute was called with the correct SQL and parameters
        mock_cursor.execute.assert_called_once()
        args, kwargs = mock_cursor.execute.call_args
        sql = args[0]
        params = args[1]
        
        assert "SELECT zodiac_sign FROM user_settings WHERE user_id = ?" in sql
        assert params == (12345,)
        
        # Verify that fetchone was called
        mock_cursor.fetchone.assert_called_once()
        
        # Verify that the zodiac sign was returned
        assert result == "овен"
    
    def test_get_user_zodiac_not_exists(self, mock_logger, mock_sqlite3):
        """Test get_user_zodiac method with no zodiac sign"""
        _, mock_connection, mock_cursor = mock_sqlite3
        
        # Mock cursor.fetchone to return None
        mock_cursor.fetchone.return_value = None
        
        # Create a database instance
        db = Database("test.db")
        
        # Reset the mocks to test get_user_zodiac directly
        mock_connection.cursor.reset_mock()
        mock_cursor.execute.reset_mock()
        mock_cursor.fetchone.reset_mock()
        
        # Call get_user_zodiac
        result = db.get_user_zodiac(12345)
        
        # Verify that cursor was created
        mock_connection.cursor.assert_called_once()
        
        # Verify that execute was called with the correct SQL and parameters
        mock_cursor.execute.assert_called_once()
        
        # Verify that fetchone was called
        mock_cursor.fetchone.assert_called_once()
        
        # Verify that None was returned
        assert result is None
