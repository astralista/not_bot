import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from src.bot.handlers.medication_handlers import MedicationHandlers, NAME, DOSE, INTAKES, START_DATE, DURATION_VALUE, DURATION_UNIT, BREAK_VALUE, BREAK_UNIT, CYCLES, EDIT_CHOICE, EDIT_FIELD, ZODIAC_SIGN


class TestMedicationHandlersAdditional:
    """Additional tests for the MedicationHandlers class to improve coverage"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_db = MagicMock()
        self.mock_logger = MagicMock()
        self.handlers = MedicationHandlers(self.mock_db, self.mock_logger)
    
    @pytest.mark.asyncio
    async def test_edit_medication_with_medications(self, mock_update, mock_context):
        """Test edit_medication with existing medications"""
        # Mock the database to return some medications
        self.mock_db.get_medications.return_value = [
            (1, 12345, "Med1", 2, 3, "2025-01-01", 10, "days", 5, "days", 2),
            (2, 12345, "Med2", 1, 2, "2025-02-01", 20, "days", 10, "days", 1)
        ]
        
        # Call the method
        result = await self.handlers.edit_medication(mock_update, mock_context)
        
        # Verify that the database was queried with the correct user ID
        self.mock_db.get_medications.assert_called_once_with(mock_update.effective_user.id)
        
        # Verify that a reply was sent with the list of medications
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message asks to select a medication
        assert "Выберите лекарство для редактирования" in args[0]
        
        # Check that the keyboard markup was included with the correct buttons
        assert isinstance(kwargs['reply_markup'], InlineKeyboardMarkup)
        keyboard = kwargs['reply_markup'].inline_keyboard
        assert len(keyboard) == 2
        assert keyboard[0][0].text == "Med1 (ID: 1)"
        assert keyboard[0][0].callback_data == "edit_1"
        assert keyboard[1][0].text == "Med2 (ID: 2)"
        assert keyboard[1][0].callback_data == "edit_2"
        
        # Check that the conversation continues to EDIT_CHOICE state
        assert result == EDIT_CHOICE
    
    @pytest.mark.asyncio
    async def test_edit_medication_no_medications(self, mock_update, mock_context):
        """Test edit_medication with no medications"""
        # Mock the database to return no medications
        self.mock_db.get_medications.return_value = []
        
        # Call the method
        result = await self.handlers.edit_medication(mock_update, mock_context)
        
        # Verify that the database was queried with the correct user ID
        self.mock_db.get_medications.assert_called_once_with(mock_update.effective_user.id)
        
        # Verify that a reply was sent indicating no medications
        mock_update.message.reply_text.assert_called_once_with("ℹ️ Нет лекарств для редактирования.")
        
        # Check that the conversation ended
        assert result == ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_edit_choice_valid(self, mock_update, mock_context):
        """Test edit_choice with valid medication ID"""
        # Set up the callback query
        mock_update.callback_query.data = "edit_1"
        
        # Mock the database to return a medication
        self.mock_db.get_medication_by_id.return_value = (
            1, 12345, "Test Med", 2, 3, "2025-01-01", 10, "days", 5, "days", 2
        )
        
        # Call the method
        result = await self.handlers.edit_choice(mock_update, mock_context)
        
        # Verify that the callback query was answered
        mock_update.callback_query.answer.assert_called_once()
        
        # Verify that the medication ID was stored in user_data
        assert mock_context.user_data["edit_id"] == 1
        
        # Verify that the database was queried with the correct medication ID
        self.mock_db.get_medication_by_id.assert_called_once_with(1)
        
        # Verify that the message was edited with the field selection keyboard
        mock_update.callback_query.edit_message_text.assert_called_once()
        args, kwargs = mock_update.callback_query.edit_message_text.call_args
        
        # Check that the message asks to select a field
        assert "Что именно хотите изменить?" in args[0]
        
        # Check that the keyboard markup was included with the correct buttons
        assert isinstance(kwargs['reply_markup'], InlineKeyboardMarkup)
        keyboard = kwargs['reply_markup'].inline_keyboard
        assert len(keyboard) == 9  # 9 fields to edit
        
        # Check that the conversation continues to EDIT_FIELD state
        assert result == EDIT_FIELD
    
    @pytest.mark.asyncio
    async def test_edit_choice_invalid(self, mock_update, mock_context):
        """Test edit_choice with invalid medication ID"""
        # Set up the callback query
        mock_update.callback_query.data = "edit_999"
        
        # Mock the database to return None (medication not found)
        self.mock_db.get_medication_by_id.return_value = None
        
        # Call the method
        result = await self.handlers.edit_choice(mock_update, mock_context)
        
        # Verify that the callback query was answered
        mock_update.callback_query.answer.assert_called_once()
        
        # Verify that the database was queried with the correct medication ID
        self.mock_db.get_medication_by_id.assert_called_once_with(999)
        
        # Verify that the message was edited to indicate an error
        mock_update.callback_query.edit_message_text.assert_called_once_with("❌ Лекарство не найдено")
        
        # Check that the conversation ended
        assert result == ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_edit_choice_exception(self, mock_update, mock_context):
        """Test edit_choice with exception during message editing"""
        # Set up the callback query
        mock_update.callback_query.data = "edit_1"
        
        # Mock the database to return a medication
        self.mock_db.get_medication_by_id.return_value = (
            1, 12345, "Test Med", 2, 3, "2025-01-01", 10, "days", 5, "days", 2
        )
        
        # Mock the edit_message_text method to raise an exception
        mock_update.callback_query.edit_message_text.side_effect = Exception("Test error")
        
        # Call the method
        result = await self.handlers.edit_choice(mock_update, mock_context)
        
        # Verify that the callback query was answered
        mock_update.callback_query.answer.assert_called_once()
        
        # Verify that the medication ID was stored in user_data
        assert mock_context.user_data["edit_id"] == 1
        
        # Verify that the database was queried with the correct medication ID
        self.mock_db.get_medication_by_id.assert_called_once_with(1)
        
        # Verify that the error was logged
        self.mock_logger.getChild().error.assert_called_once()
        
        # Check that the conversation ended
        assert result == ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_handle_field_selection(self, mock_update, mock_context):
        """Test handle_field_selection"""
        # Set up the callback query
        mock_update.callback_query.data = "name"
        
        # Call the method
        result = await self.handlers.handle_field_selection(mock_update, mock_context)
        
        # Verify that the callback query was answered
        mock_update.callback_query.answer.assert_called_once()
        
        # Verify that the field was stored in user_data
        assert mock_context.user_data["edit_field"] == "name"
        
        # Verify that the message was edited to ask for the new value
        mock_update.callback_query.edit_message_text.assert_called_once()
        args, kwargs = mock_update.callback_query.edit_message_text.call_args
        
        # Check that the message asks for the new value
        assert "Введите новое значение для название" in args[0]
        
        # Check that the conversation continues to EDIT_FIELD state
        assert result == EDIT_FIELD
    
    @pytest.mark.asyncio
    async def test_save_edit_name_valid(self, mock_update, mock_context):
        """Test save_edit with valid name"""
        # Set up the message text
        mock_update.message.text = "New Med Name"
        
        # Set up user_data
        mock_context.user_data = {
            "edit_id": 1,
            "edit_field": "name"
        }
        
        # Mock the database to return a medication
        self.mock_db.get_medication_by_id.return_value = (
            1, 12345, "Test Med", 2, 3, "2025-01-01", 10, "days", 5, "days", 2
        )
        
        # Call the method
        result = await self.handlers.save_edit(mock_update, mock_context)
        
        # Verify that the database was queried with the correct medication ID
        self.mock_db.get_medication_by_id.assert_called()
        
        # Verify that the database was updated with the new value
        self.mock_db.update_medication.assert_called_once_with(1, **{"name": "New Med Name"})
        
        # Verify that a success reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates success
        assert "успешно обновлено" in args[0]
        
        # Check that the user_data was cleared
        assert "edit_id" not in mock_context.user_data
        assert "edit_field" not in mock_context.user_data
        
        # Check that the conversation ended
        assert result == ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_save_edit_name_too_long(self, mock_update, mock_context):
        """Test save_edit with name that is too long"""
        # Set up the message text
        mock_update.message.text = "A" * 51  # 51 characters
        
        # Set up user_data
        mock_context.user_data = {
            "edit_id": 1,
            "edit_field": "name"
        }
        
        # Mock the database to return a medication
        self.mock_db.get_medication_by_id.return_value = (
            1, 12345, "Test Med", 2, 3, "2025-01-01", 10, "days", 5, "days", 2
        )
        
        # Call the method
        result = await self.handlers.save_edit(mock_update, mock_context)
        
        # Verify that the database was queried with the correct medication ID
        self.mock_db.get_medication_by_id.assert_called_once_with(1)
        
        # Verify that the database was not updated
        self.mock_db.update_medication.assert_not_called()
        
        # Verify that an error reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates an error
        assert "Название слишком длинное" in args[0]
        
        # Check that the conversation continues in EDIT_FIELD state
        assert result == EDIT_FIELD
    
    @pytest.mark.asyncio
    async def test_save_edit_dose_valid(self, mock_update, mock_context):
        """Test save_edit with valid dose"""
        # Set up the message text
        mock_update.message.text = "3"
        
        # Set up user_data
        mock_context.user_data = {
            "edit_id": 1,
            "edit_field": "dose"
        }
        
        # Mock the database to return a medication
        self.mock_db.get_medication_by_id.return_value = (
            1, 12345, "Test Med", 2, 3, "2025-01-01", 10, "days", 5, "days", 2
        )
        
        # Call the method
        result = await self.handlers.save_edit(mock_update, mock_context)
        
        # Verify that the database was queried with the correct medication ID
        self.mock_db.get_medication_by_id.assert_called()
        
        # Verify that the database was updated with the new value
        self.mock_db.update_medication.assert_called_once_with(1, **{"dose": 3})
        
        # Verify that a success reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates success
        assert "успешно обновлено" in args[0]
        
        # Check that the conversation ended
        assert result == ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_save_edit_dose_invalid(self, mock_update, mock_context):
        """Test save_edit with invalid dose"""
        # Set up the message text
        mock_update.message.text = "abc"
        
        # Set up user_data
        mock_context.user_data = {
            "edit_id": 1,
            "edit_field": "dose"
        }
        
        # Mock the database to return a medication
        self.mock_db.get_medication_by_id.return_value = (
            1, 12345, "Test Med", 2, 3, "2025-01-01", 10, "days", 5, "days", 2
        )
        
        # Call the method
        result = await self.handlers.save_edit(mock_update, mock_context)
        
        # Verify that the database was queried with the correct medication ID
        self.mock_db.get_medication_by_id.assert_called_once_with(1)
        
        # Verify that the database was not updated
        self.mock_db.update_medication.assert_not_called()
        
        # Verify that an error reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates an error
        assert "Должно быть целое число" in args[0]
        
        # Check that the conversation continues in EDIT_FIELD state
        assert result == EDIT_FIELD
    
    @pytest.mark.asyncio
    async def test_save_edit_duration_unit_valid(self, mock_update, mock_context):
        """Test save_edit with valid duration unit"""
        # Set up the message text
        mock_update.message.text = "months"
        
        # Set up user_data
        mock_context.user_data = {
            "edit_id": 1,
            "edit_field": "duration_unit"
        }
        
        # Mock the database to return a medication
        self.mock_db.get_medication_by_id.return_value = (
            1, 12345, "Test Med", 2, 3, "2025-01-01", 10, "days", 5, "days", 2
        )
        
        # Call the method
        result = await self.handlers.save_edit(mock_update, mock_context)
        
        # Verify that the database was queried with the correct medication ID
        self.mock_db.get_medication_by_id.assert_called()
        
        # Verify that the database was updated with the new value
        self.mock_db.update_medication.assert_called_once_with(1, **{"duration_unit": "months"})
        
        # Verify that a success reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates success
        assert "успешно обновлено" in args[0]
        
        # Check that the conversation ended
        assert result == ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_save_edit_duration_unit_invalid(self, mock_update, mock_context):
        """Test save_edit with invalid duration unit"""
        # Set up the message text
        mock_update.message.text = "weeks"
        
        # Set up user_data
        mock_context.user_data = {
            "edit_id": 1,
            "edit_field": "duration_unit"
        }
        
        # Mock the database to return a medication
        self.mock_db.get_medication_by_id.return_value = (
            1, 12345, "Test Med", 2, 3, "2025-01-01", 10, "days", 5, "days", 2
        )
        
        # Call the method
        result = await self.handlers.save_edit(mock_update, mock_context)
        
        # Verify that the database was queried with the correct medication ID
        self.mock_db.get_medication_by_id.assert_called_once_with(1)
        
        # Verify that the database was not updated
        self.mock_db.update_medication.assert_not_called()
        
        # Verify that an error reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates an error
        assert "Допустимые значения: 'days' или 'months'" in args[0]
        
        # Check that the conversation continues in EDIT_FIELD state
        assert result == EDIT_FIELD
    
    @pytest.mark.asyncio
    async def test_save_edit_start_date_valid(self, mock_update, mock_context):
        """Test save_edit with valid start date"""
        # Set up the message text
        mock_update.message.text = "2025-02-01"
        
        # Set up user_data
        mock_context.user_data = {
            "edit_id": 1,
            "edit_field": "start_date"
        }
        
        # Mock the database to return a medication
        self.mock_db.get_medication_by_id.return_value = (
            1, 12345, "Test Med", 2, 3, "2025-01-01", 10, "days", 5, "days", 2
        )
        
        # Call the method
        result = await self.handlers.save_edit(mock_update, mock_context)
        
        # Verify that the database was queried with the correct medication ID
        self.mock_db.get_medication_by_id.assert_called()
        
        # Verify that the database was updated with the new value
        self.mock_db.update_medication.assert_called_once_with(1, **{"start_date": "2025-02-01"})
        
        # Verify that a success reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates success
        assert "успешно обновлено" in args[0]
        
        # Check that the conversation ended
        assert result == ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_save_edit_start_date_invalid(self, mock_update, mock_context):
        """Test save_edit with invalid start date"""
        # Set up the message text
        mock_update.message.text = "01-02-2025"  # Wrong format
        
        # Set up user_data
        mock_context.user_data = {
            "edit_id": 1,
            "edit_field": "start_date"
        }
        
        # Mock the database to return a medication
        self.mock_db.get_medication_by_id.return_value = (
            1, 12345, "Test Med", 2, 3, "2025-01-01", 10, "days", 5, "days", 2
        )
        
        # Call the method
        result = await self.handlers.save_edit(mock_update, mock_context)
        
        # Verify that the database was queried with the correct medication ID
        self.mock_db.get_medication_by_id.assert_called_once_with(1)
        
        # Verify that the database was not updated
        self.mock_db.update_medication.assert_not_called()
        
        # Verify that an error reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates an error
        assert "Неверный формат даты" in args[0]
        
        # Check that the conversation continues in EDIT_FIELD state
        assert result == EDIT_FIELD
    
    @pytest.mark.asyncio
    async def test_save_edit_missing_context_data(self, mock_update, mock_context):
        """Test save_edit with missing context data"""
        # Set up the message text
        mock_update.message.text = "New Value"
        
        # Set up user_data with missing fields
        mock_context.user_data = {}
        
        # Call the method
        result = await self.handlers.save_edit(mock_update, mock_context)
        
        # Verify that the database was not queried
        self.mock_db.get_medication_by_id.assert_not_called()
        
        # Verify that the database was not updated
        self.mock_db.update_medication.assert_not_called()
        
        # Verify that an error reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates an error
        assert "Сессия редактирования устарела" in args[0]
        
        # Check that the conversation ended
        assert result == ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_save_edit_medication_not_found(self, mock_update, mock_context):
        """Test save_edit with medication not found"""
        # Set up the message text
        mock_update.message.text = "New Value"
        
        # Set up user_data
        mock_context.user_data = {
            "edit_id": 999,
            "edit_field": "name"
        }
        
        # Mock the database to return None (medication not found)
        self.mock_db.get_medication_by_id.return_value = None
        
        # Call the method
        result = await self.handlers.save_edit(mock_update, mock_context)
        
        # Verify that the database was queried with the correct medication ID
        self.mock_db.get_medication_by_id.assert_called_once_with(999)
        
        # Verify that the database was not updated
        self.mock_db.update_medication.assert_not_called()
        
        # Verify that an error reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates an error
        assert "Лекарство не найдено" in args[0]
        
        # Check that the conversation ended
        assert result == ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_save_edit_database_error(self, mock_update, mock_context):
        """Test save_edit with database error"""
        # Set up the message text
        mock_update.message.text = "New Med Name"
        
        # Set up user_data
        mock_context.user_data = {
            "edit_id": 1,
            "edit_field": "name"
        }
        
        # Mock the database to return a medication
        self.mock_db.get_medication_by_id.return_value = (
            1, 12345, "Test Med", 2, 3, "2025-01-01", 10, "days", 5, "days", 2
        )
        
        # Mock the database to raise an exception
        self.mock_db.update_medication.side_effect = Exception("Database error")
        
        # Call the method
        result = await self.handlers.save_edit(mock_update, mock_context)
        
        # Verify that the database was queried with the correct medication ID
        self.mock_db.get_medication_by_id.assert_called_once_with(1)
        
        # Verify that an attempt was made to update the database
        self.mock_db.update_medication.assert_called_once()
        
        # Verify that an error reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates an error
        assert "Произошла ошибка при сохранении" in args[0]
        
        # Check that the error was logged
        self.mock_logger.getChild().error.assert_called_once()
        
        # Check that the conversation ended
        assert result == ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_delete_medication_with_medications(self, mock_update, mock_context):
        """Test delete_medication with existing medications"""
        # Mock the database to return some medications
        self.mock_db.get_medications.return_value = [
            (1, 12345, "Med1", 2, 3, "2025-01-01", 10, "days", 5, "days", 2),
            (2, 12345, "Med2", 1, 2, "2025-02-01", 20, "days", 10, "days", 1)
        ]
        
        # Call the method
        await self.handlers.delete_medication(mock_update, mock_context)
        
        # Verify that the database was queried with the correct user ID
        self.mock_db.get_medications.assert_called_once_with(mock_update.message.from_user.id)
        
        # Verify that a reply was sent with the list of medications
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message asks to select a medication
        assert "Выберите лекарство для удаления" in args[0]
        
        # Check that the keyboard markup was included with the correct buttons
        assert isinstance(kwargs['reply_markup'], InlineKeyboardMarkup)
        keyboard = kwargs['reply_markup'].inline_keyboard
        assert len(keyboard) == 2
        assert keyboard[0][0].text == "Med1 (ID: 1)"
        assert keyboard[0][0].callback_data == "delete_1"
        assert keyboard[1][0].text == "Med2 (ID: 2)"
        assert keyboard[1][0].callback_data == "delete_2"
    
    @pytest.mark.asyncio
    async def test_delete_medication_no_medications(self, mock_update, mock_context):
        """Test delete_medication with no medications"""
        # Mock the database to return no medications
        self.mock_db.get_medications.return_value = []
        
        # Call the method
        await self.handlers.delete_medication(mock_update, mock_context)
        
        # Verify that the database was queried with the correct user ID
        self.mock_db.get_medications.assert_called_once_with(mock_update.message.from_user.id)
        
        # Verify that a reply was sent indicating no medications
        mock_update.message.reply_text.assert_called_once_with("ℹ️ Нет лекарств для удаления.")
    
    @pytest.mark.asyncio
    async def test_delete_confirm(self, mock_update, mock_context):
        """Test delete_confirm"""
        # Set up the callback query
        mock_update.callback_query.data = "delete_1"
        
        # Call the method
        await self.handlers.delete_confirm(mock_update, mock_context)
        
        # Verify that the callback query was answered
        mock_update.callback_query.answer.assert_called_once()
        
        # Verify that the database was updated to delete the medication
        self.mock_db.delete_medication.assert_called_once_with(1)
        
        # Verify that the message was edited to indicate success
        mock_update.callback_query.edit_message_text.assert_called_once_with("✅ Лекарство удалено!")
    
    @pytest.mark.asyncio
    async def test_list_medications_with_medications(self, mock_update, mock_context):
        """Test list_medications with existing medications"""
        # Mock the database to return some medications
        self.mock_db.get_medications.return_value = [
            (1, 12345, "Med1", 2, 3, "2025-01-01", 10, "days", 5, "days", 2),
            (2, 12345, "Med2", 1, 2, "2025-02-01", 20, "days", 10, "days", 1)
        ]
        
        # Mock the format_medication_info function
        with patch('src.bot.handlers.medication_handlers.format_medication_info') as mock_format:
            mock_format.side_effect = ["Formatted Med1", "Formatted Med2"]
            
            # Call the method
            await self.handlers.list_medications(mock_update, mock_context)
            
            # Verify that the database was queried with the correct user ID
            self.mock_db.get_medications.assert_called_once_with(mock_update.message.from_user.id)
            
            # Verify that format_medication_info was called for each medication
            assert mock_format.call_count == 2
            
            # Verify that a reply was sent with the list of medications
            mock_update.message.reply_text.assert_called_once()
            args, kwargs = mock_update.message.reply_text.call_args
            
            # Check that the message contains the medications
            assert "Ваши лекарства" in args[0]
            assert "Formatted Med1" in args[0]
            assert "Formatted Med2" in args[0]
            
            # Check that parse_mode is HTML
            assert kwargs.get('parse_mode') == "HTML"
    
    @pytest.mark.asyncio
    async def test_list_medications_no_medications(self, mock_update, mock_context):
        """Test list_medications with no medications"""
        # Mock the database to return no medications
        self.mock_db.get_medications.return_value = []
        
        # Call the method
        await self.handlers.list_medications(mock_update, mock_context)
        
        # Verify that the database was queried with the correct user ID
        self.mock_db.get_medications.assert_called_once_with(mock_update.message.from_user.id)
        
        # Verify that a reply was sent indicating no medications
        mock_update.message.reply_text.assert_called_once_with("ℹ️ У вас пока нет добавленных лекарств.")
    
    @pytest.mark.asyncio
    async def test_list_medications_format_error(self, mock_update, mock_context):
        """Test list_medications with error during formatting"""
        # Mock the database to return some medications
        self.mock_db.get_medications.return_value = [
            (1, 12345, "Med1", 2, 3, "2025-01-01", 10, "days", 5, "days", 2)
        ]
        
        # Mock the format_medication_info function to raise an exception
        with patch('src.bot.handlers.medication_handlers.format_medication_info') as mock_format:
            mock_format.side_effect = Exception("Format error")
            
            # Call the method
            await self.handlers.list_medications(mock_update, mock_context)
            
            # Verify that the database was queried with the correct user ID
            self.mock_db.get_medications.assert_called_once_with(mock_update.message.from_user.id)
            
            # Verify that format_medication_info was called
            mock_format.assert_called_once()
            
            # Verify that a reply was sent with an error message for the medication
            mock_update.message.reply_text.assert_called_once()
            args, kwargs = mock_update.message.reply_text.call_args
            
            # Check that the message contains the error indicator
            assert "Ваши лекарства" in args[0]
            assert "ошибка данных" in args[0]
            
            # Check that parse_mode is HTML
            assert kwargs.get('parse_mode') == "HTML"
    
    @pytest.mark.asyncio
    async def test_list_medications_database_error(self, mock_update, mock_context):
        """Test list_medications with database error"""
        # Mock the database to raise an exception
        self.mock_db.get_medications.side_effect = Exception("Database error")
        
        # Call the method
        await self.handlers.list_medications(mock_update, mock_context)
        
        # Verify that an attempt was made to query the database
        self.mock_db.get_medications.assert_called_once()
        
        # Verify that the error was logged
        self.mock_logger.getChild().error.assert_called_once()
        
        # Verify that a reply was sent with an error message
        mock_update.message.reply_text.assert_called_once_with("❌ Произошла ошибка при загрузке данных. Попробуйте позже.")
