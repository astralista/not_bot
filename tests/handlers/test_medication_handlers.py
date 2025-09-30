import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from src.bot.handlers.medication_handlers import MedicationHandlers, NAME, DOSE, INTAKES, START_DATE, DURATION_VALUE, DURATION_UNIT, BREAK_VALUE, BREAK_UNIT, CYCLES, EDIT_CHOICE, EDIT_FIELD, ZODIAC_SIGN


class TestMedicationHandlers:
    """Tests for the MedicationHandlers class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_db = MagicMock()
        self.mock_logger = MagicMock()
        self.handlers = MedicationHandlers(self.mock_db, self.mock_logger)
    
    @pytest.mark.asyncio
    async def test_start_existing_user(self, mock_update, mock_context):
        """Test start command with existing user"""
        # Mock the database to return a zodiac sign
        self.mock_db.get_user_zodiac.return_value = "овен"
        
        # Call the method
        result = await self.handlers.start(mock_update, mock_context)
        
        # Verify that get_user_zodiac was called
        self.mock_db.get_user_zodiac.assert_called_once_with(mock_update.effective_user.id)
        
        # Verify that a reply was sent with the main menu
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message contains the menu
        assert "Бот-напоминатель о лекарствах" in args[0]
        assert "Выберите действие" in args[0]
        
        # Check that the keyboard was included
        assert "reply_markup" in kwargs
        assert isinstance(kwargs["reply_markup"], ReplyKeyboardMarkup)
        
        # Check that the conversation ended
        assert result == ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_start_new_user(self, mock_update, mock_context):
        """Test start command with new user"""
        # Mock the database to return no zodiac sign
        self.mock_db.get_user_zodiac.return_value = None
        
        # Call the method
        result = await self.handlers.start(mock_update, mock_context)
        
        # Verify that get_user_zodiac was called
        self.mock_db.get_user_zodiac.assert_called_once_with(mock_update.effective_user.id)
        
        # Verify that a reply was sent with the zodiac sign prompt
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message contains the zodiac sign prompt
        assert "Привет!" in args[0]
        assert "знак зодиака" in args[0]
        
        # Check that the conversation moved to ZODIAC_SIGN state
        assert result == ZODIAC_SIGN
    
    @pytest.mark.asyncio
    async def test_set_user_zodiac_valid(self, mock_update, mock_context):
        """Test set_user_zodiac with valid zodiac sign"""
        # Set up the message text
        mock_update.message.text = "овен"
        
        # Call the method
        result = await self.handlers.set_user_zodiac(mock_update, mock_context)
        
        # Verify that add_user_settings was called
        self.mock_db.add_user_settings.assert_called_once_with(mock_update.effective_user.id, "овен")
        
        # Verify that two replies were sent
        assert mock_update.message.reply_text.call_count == 2
        
        # Check the first reply
        args1, kwargs1 = mock_update.message.reply_text.call_args_list[0]
        assert "Отлично!" in args1[0]
        assert "Овен" in args1[0]
        
        # Check the second reply
        args2, kwargs2 = mock_update.message.reply_text.call_args_list[1]
        assert "Бот-напоминатель о лекарствах" in args2[0]
        assert "reply_markup" in kwargs2
        
        # Check that the conversation ended
        assert result == ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_set_user_zodiac_invalid(self, mock_update, mock_context):
        """Test set_user_zodiac with invalid zodiac sign"""
        # Set up the message text
        mock_update.message.text = "invalid"
        
        # Call the method
        result = await self.handlers.set_user_zodiac(mock_update, mock_context)
        
        # Verify that add_user_settings was not called
        self.mock_db.add_user_settings.assert_not_called()
        
        # Verify that a reply was sent with an error message
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message contains the error
        assert "Неверный знак зодиака" in args[0]
        
        # Check that the conversation stayed in ZODIAC_SIGN state
        assert result == ZODIAC_SIGN
    
    @pytest.mark.asyncio
    async def test_set_user_zodiac_error(self, mock_update, mock_context):
        """Test set_user_zodiac with database error"""
        # Set up the message text
        mock_update.message.text = "овен"
        
        # Mock the database to raise an exception
        self.mock_db.add_user_settings.side_effect = Exception("Database error")
        
        # Call the method
        result = await self.handlers.set_user_zodiac(mock_update, mock_context)
        
        # Verify that add_user_settings was called
        self.mock_db.add_user_settings.assert_called_once()
        
        # Verify that the error was logged
        self.mock_logger.getChild().error.assert_called_once()
        
        # Verify that a reply was sent with an error message
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message contains the error
        assert "Произошла ошибка при сохранении" in args[0]
        
        # Check that the conversation ended
        assert result == ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_add_medication(self, mock_update, mock_context):
        """Test add_medication method"""
        # Call the method
        result = await self.handlers.add_medication(mock_update, mock_context)
        
        # Verify that a reply was sent
        mock_update.message.reply_text.assert_called_once_with("Введите название лекарства:")
        
        # Check that the conversation moved to NAME state
        assert result == NAME
    
    @pytest.mark.asyncio
    async def test_set_name_valid(self, mock_update, mock_context):
        """Test set_name with valid name"""
        # Set up the message text
        mock_update.message.text = "Аспирин"
        
        # Call the method
        result = await self.handlers.set_name(mock_update, mock_context)
        
        # Verify that the name was saved in user_data
        assert mock_context.user_data["name"] == "Аспирин"
        
        # Verify that a reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message asks for the dose
        assert "капсул за один прием" in args[0]
        
        # Check that the conversation moved to DOSE state
        assert result == DOSE
    
    @pytest.mark.asyncio
    async def test_set_name_empty(self, mock_update, mock_context):
        """Test set_name with empty name"""
        # Set up the message text
        mock_update.message.text = ""
        
        # Call the method
        result = await self.handlers.set_name(mock_update, mock_context)
        
        # Verify that a reply was sent with an error message
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message contains the error
        assert "Название не может быть пустым" in args[0]
        
        # Check that the conversation stayed in NAME state
        assert result == NAME
    
    @pytest.mark.asyncio
    async def test_set_name_too_long(self, mock_update, mock_context):
        """Test set_name with too long name"""
        # Set up the message text
        mock_update.message.text = "A" * 51  # 51 characters
        
        # Call the method
        result = await self.handlers.set_name(mock_update, mock_context)
        
        # Verify that a reply was sent with an error message
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message contains the error
        assert "Название слишком длинное" in args[0]
        
        # Check that the conversation stayed in NAME state
        assert result == NAME
    
    @pytest.mark.asyncio
    async def test_set_dose_valid(self, mock_update, mock_context):
        """Test set_dose with valid dose"""
        # Set up the message text
        mock_update.message.text = "2"
        
        # Call the method
        result = await self.handlers.set_dose(mock_update, mock_context)
        
        # Verify that the dose was saved in user_data
        assert mock_context.user_data["dose"] == 2
        
        # Verify that a reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message asks for the intakes
        assert "Сколько приемов в сутки" in args[0]
        
        # Check that the conversation moved to INTAKES state
        assert result == INTAKES
    
    @pytest.mark.asyncio
    async def test_set_dose_invalid(self, mock_update, mock_context):
        """Test set_dose with invalid dose"""
        # Set up the message text
        mock_update.message.text = "abc"
        
        # Call the method
        result = await self.handlers.set_dose(mock_update, mock_context)
        
        # Verify that a reply was sent with an error message
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message contains the error
        assert "Должно быть целое число больше 0" in args[0]
        
        # Check that the conversation stayed in DOSE state
        assert result == DOSE
    
    @pytest.mark.asyncio
    async def test_set_intakes_valid(self, mock_update, mock_context):
        """Test set_intakes with valid intakes"""
        # Set up the message text
        mock_update.message.text = "3"
        
        # Call the method
        result = await self.handlers.set_intakes(mock_update, mock_context)
        
        # Verify that the intakes was saved in user_data
        assert mock_context.user_data["intakes"] == 3
        
        # Verify that a reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message asks for the start date
        assert "Дата начала приема" in args[0]
        
        # Check that the conversation moved to START_DATE state
        assert result == START_DATE
    
    @pytest.mark.asyncio
    async def test_set_intakes_invalid(self, mock_update, mock_context):
        """Test set_intakes with invalid intakes"""
        # Set up the message text
        mock_update.message.text = "0"
        
        # Call the method
        result = await self.handlers.set_intakes(mock_update, mock_context)
        
        # Verify that a reply was sent with an error message
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message contains the error
        assert "Должно быть целое число от 1 до 24" in args[0]
        
        # Check that the conversation stayed in INTAKES state
        assert result == INTAKES
    
    @pytest.mark.asyncio
    async def test_set_start_date_valid(self, mock_update, mock_context):
        """Test set_start_date with valid date"""
        # Set up the message text
        mock_update.message.text = "2025-01-01"
        
        # Call the method
        result = await self.handlers.set_start_date(mock_update, mock_context)
        
        # Verify that the start_date was saved in user_data
        assert mock_context.user_data["start_date"] == "2025-01-01"
        
        # Verify that a reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message asks for the duration value
        assert "Длительность приема" in args[0]
        
        # Check that the conversation moved to DURATION_VALUE state
        assert result == DURATION_VALUE
    
    @pytest.mark.asyncio
    async def test_set_start_date_invalid(self, mock_update, mock_context):
        """Test set_start_date with invalid date"""
        # Set up the message text
        mock_update.message.text = "01-01-2025"
        
        # Call the method
        result = await self.handlers.set_start_date(mock_update, mock_context)
        
        # Verify that a reply was sent with an error message
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message contains the error
        assert "Неверный формат даты" in args[0]
        
        # Check that the conversation stayed in START_DATE state
        assert result == START_DATE
    
    @pytest.mark.asyncio
    async def test_set_duration_value_valid(self, mock_update, mock_context):
        """Test set_duration_value with valid value"""
        # Set up the message text
        mock_update.message.text = "30"
        
        # Call the method
        result = await self.handlers.set_duration_value(mock_update, mock_context)
        
        # Verify that the duration_value was saved in user_data
        assert mock_context.user_data["duration_value"] == 30
        
        # Verify that a reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message asks for the duration unit
        assert "Выберите единицы измерения" in args[0]
        
        # Check that the conversation moved to DURATION_UNIT state
        assert result == DURATION_UNIT
    
    @pytest.mark.asyncio
    async def test_set_duration_value_invalid(self, mock_update, mock_context):
        """Test set_duration_value with invalid value"""
        # Set up the message text
        mock_update.message.text = "0"
        
        # Call the method
        result = await self.handlers.set_duration_value(mock_update, mock_context)
        
        # Verify that a reply was sent with an error message
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message contains the error
        assert "Должно быть целое число больше 0" in args[0]
        
        # Check that the conversation stayed in DURATION_VALUE state
        assert result == DURATION_VALUE
    
    @pytest.mark.asyncio
    async def test_set_duration_unit_valid(self, mock_update, mock_context):
        """Test set_duration_unit with valid unit"""
        # Set up the message text
        mock_update.message.text = "days"
        
        # Call the method
        result = await self.handlers.set_duration_unit(mock_update, mock_context)
        
        # Verify that the duration_unit was saved in user_data
        assert mock_context.user_data["duration_unit"] == "days"
        
        # Verify that a reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message asks for the break value
        assert "Длительность перерыва между курсами" in args[0]
        
        # Check that the conversation moved to BREAK_VALUE state
        assert result == BREAK_VALUE
    
    @pytest.mark.asyncio
    async def test_set_duration_unit_invalid(self, mock_update, mock_context):
        """Test set_duration_unit with invalid unit"""
        # Set up the message text
        mock_update.message.text = "weeks"
        
        # Call the method
        result = await self.handlers.set_duration_unit(mock_update, mock_context)
        
        # Verify that a reply was sent with an error message
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message contains the error
        assert "Некорректный формат" in args[0]
        
        # Check that the conversation stayed in DURATION_UNIT state
        assert result == DURATION_UNIT
    
    @pytest.mark.asyncio
    async def test_set_break_value_valid(self, mock_update, mock_context):
        """Test set_break_value with valid value"""
        # Set up the message text
        mock_update.message.text = "5"
        
        # Call the method
        result = await self.handlers.set_break_value(mock_update, mock_context)
        
        # Verify that the break_value was saved in user_data
        assert mock_context.user_data["break_value"] == 5
        
        # Verify that a reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message asks for the break unit
        assert "Выберите единицы измерения для перерыва" in args[0]
        
        # Check that the conversation moved to BREAK_UNIT state
        assert result == BREAK_UNIT
    
    @pytest.mark.asyncio
    async def test_set_break_value_invalid(self, mock_update, mock_context):
        """Test set_break_value with invalid value"""
        # Set up the message text
        mock_update.message.text = "-1"
        
        # Call the method
        result = await self.handlers.set_break_value(mock_update, mock_context)
        
        # Verify that a reply was sent with an error message
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message contains the error
        assert "Должно быть целое число 0 или больше" in args[0]
        
        # Check that the conversation stayed in BREAK_VALUE state
        assert result == BREAK_VALUE
    
    @pytest.mark.asyncio
    async def test_set_break_unit_valid(self, mock_update, mock_context):
        """Test set_break_unit with valid unit"""
        # Set up the message text
        mock_update.message.text = "days"
        
        # Call the method
        result = await self.handlers.set_break_unit(mock_update, mock_context)
        
        # Verify that the break_unit was saved in user_data
        assert mock_context.user_data["break_unit"] == "days"
        
        # Verify that a reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message asks for the cycles
        assert "Сколько всего курсов" in args[0]
        
        # Check that the conversation moved to CYCLES state
        assert result == CYCLES
    
    @pytest.mark.asyncio
    async def test_set_break_unit_invalid(self, mock_update, mock_context):
        """Test set_break_unit with invalid unit"""
        # Set up the message text
        mock_update.message.text = "weeks"
        
        # Call the method
        result = await self.handlers.set_break_unit(mock_update, mock_context)
        
        # Verify that a reply was sent with an error message
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message contains the error
        assert "Некорректный формат" in args[0]
        
        # Check that the conversation stayed in BREAK_UNIT state
        assert result == BREAK_UNIT
    
    @pytest.mark.asyncio
    async def test_set_cycles_valid(self, mock_update, mock_context):
        """Test set_cycles with valid cycles"""
        # Set up the message text
        mock_update.message.text = "2"
        
        # Set up user_data with all required fields
        mock_context.user_data = {
            "name": "Аспирин",
            "dose": 2,
            "intakes": 3,
            "start_date": "2025-01-01",
            "duration_value": 30,
            "duration_unit": "days",
            "break_value": 5,
            "break_unit": "days"
        }
        
        # Call the method
        result = await self.handlers.set_cycles(mock_update, mock_context)
        
        # Verify that add_medication was called with the correct arguments
        self.mock_db.add_medication.assert_called_once_with(
            user_id=mock_update.message.from_user.id,
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
        
        # Verify that a reply was sent with a success message
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message contains the success message
        assert "Лекарство успешно добавлено" in args[0]
        
        # Check that the conversation ended
        assert result == ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_set_cycles_invalid(self, mock_update, mock_context):
        """Test set_cycles with invalid cycles"""
        # Set up the message text
        mock_update.message.text = "0"
        
        # Call the method
        result = await self.handlers.set_cycles(mock_update, mock_context)
        
        # Verify that a reply was sent with an error message
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message contains the error
        assert "Должно быть целое число больше 0" in args[0]
        
        # Check that the conversation stayed in CYCLES state
        assert result == CYCLES
    
    @pytest.mark.asyncio
    async def test_set_cycles_error(self, mock_update, mock_context):
        """Test set_cycles with database error"""
        # Set up the message text
        mock_update.message.text = "2"
        
        # Set up user_data with all required fields
        mock_context.user_data = {
            "name": "Аспирин",
            "dose": 2,
            "intakes": 3,
            "start_date": "2025-01-01",
            "duration_value": 30,
            "duration_unit": "days",
            "break_value": 5,
            "break_unit": "days"
        }
        
        # Mock the database to raise an exception
        self.mock_db.add_medication.side_effect = Exception("Database error")
        
        # Call the method
        result = await self.handlers.set_cycles(mock_update, mock_context)
        
        # Verify that add_medication was called
        self.mock_db.add_medication.assert_called_once()
        
        # Verify that the error was logged
        self.mock_logger.getChild().error.assert_called_once()
        
        # Verify that a reply was sent with an error message
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message contains the error
        assert "Произошла ошибка при сохранении" in args[0]
        
        # Check that the conversation ended
        assert result == ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_edit_medication_no_meds(self, mock_update, mock_context):
        """Test edit_medication with no medications"""
        # Mock the database to return no medications
        self.mock_db.get_medications.return_value = []
        
        # Call the method
        result = await self.handlers.edit_medication(mock_update, mock_context)
        
        # Verify that get_medications was called
        self.mock_db.get_medications.assert_called_once_with(mock_update.effective_user.id)
        
        # Verify that a reply was sent with a message
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates no medications
        assert "Нет лекарств для редактирования" in args[0]
        
        # Check that the conversation ended
        assert result == ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_edit_medication_with_meds(self, mock_update, mock_context):
        """Test edit_medication with medications"""
        # Mock the database to return medications
        med1 = (1, 12345, "Аспирин", 1, 3, "2025-01-01", 30, "days", 5, "days", 2)
        med2 = (2, 12345, "Витамин C", 2, 1, "2025-02-01", 60, "days", 0, "days", 1)
        self.mock_db.get_medications.return_value = [med1, med2]
        
        # Call the method
        result = await self.handlers.edit_medication(mock_update, mock_context)
        
        # Verify that get_medications was called
        self.mock_db.get_medications.assert_called_once_with(mock_update.effective_user.id)
        
        # Verify that a reply was sent with the medication list
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message asks to select a medication
        assert "Выберите лекарство для редактирования" in args[0]
        
        # Check that the keyboard was included
        assert "reply_markup" in kwargs
        assert isinstance(kwargs["reply_markup"], InlineKeyboardMarkup)
        
        # Check that the keyboard contains the medications
        keyboard = kwargs["reply_markup"].inline_keyboard
        assert len(keyboard) == 2
        assert "Аспирин" in keyboard[0][0].text
        assert "Витамин C" in keyboard[1][0].text
        
        # Check that the conversation moved to EDIT_CHOICE state
        assert result == EDIT_CHOICE
    
    @pytest.mark.asyncio
    async def test_edit_choice(self, mock_update, mock_context):
        """Test edit_choice method"""
        # Set up the callback query
        mock_update.callback_query.data = "edit_1"
        
        # Mock the database to return a medication
        med = (1, 12345, "Аспирин", 1, 3, "2025-01-01", 30, "days", 5, "days", 2)
        self.mock_db.get_medication_by_id.return_value = med
        
        # Call the method
        result = await self.handlers.edit_choice(mock_update, mock_context)
        
        # Verify that get_medication_by_id was called
        self.mock_db.get_medication_by_id.assert_called_once_with(1)
        
        # Verify that the medication ID was saved in user_data
        assert mock_context.user_data["edit_id"] == 1
        
        # Verify that the callback query was answered
        mock_update.callback_query.answer.assert_called_once()
        
        # Verify that the message was edited
        mock_update.callback_query.edit_message_text.assert_called_once()
        args, kwargs = mock_update.callback_query.edit_message_text.call_args
        
        # Check that the message asks what to edit
        assert "Что именно хотите изменить" in args[0]
        
        # Check that the keyboard was included
        assert "reply_markup" in kwargs
        assert isinstance(kwargs["reply_markup"], InlineKeyboardMarkup)
        
        # Check that the conversation moved to EDIT_FIELD state
        assert result == EDIT_FIELD
    
    @pytest.mark.asyncio
    async def test_edit_choice_not_found(self, mock_update, mock_context):
        """Test edit_choice with non-existent medication"""
        # Set up the callback query
        mock_update.callback_query.data = "edit_999"
        
        # Mock the database to return no medication
        self.mock_db.get_medication_by_id.return_value = None
        
        # Call the method
        result = await self.handlers.edit_choice(mock_update, mock_context)
        
        # Verify that get_medication_by_id was called
        self.mock_db.get_medication_by_id.assert_called_once_with(999)
        
        # Verify that the callback query was answered
        mock_update.callback_query
