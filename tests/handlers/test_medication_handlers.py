import pytest
from unittest.mock import MagicMock, AsyncMock, patch
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
        """Test start command for existing user"""
        # Mock the database to return a zodiac sign (existing user)
        self.mock_db.get_user_zodiac.return_value = "овен"
        
        # Call the method
        result = await self.handlers.start(mock_update, mock_context)
        
        # Verify that the database was queried with the correct user ID
        self.mock_db.get_user_zodiac.assert_called_once_with(mock_update.effective_user.id)
        
        # Verify that a reply was sent with the main menu
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message contains the bot introduction
        assert "Бот-напоминатель о лекарствах" in args[0]
        
        # Check that the keyboard markup was included
        assert isinstance(kwargs['reply_markup'], ReplyKeyboardMarkup)
        
        # Check that the conversation ended
        assert result == ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_start_new_user(self, mock_update, mock_context):
        """Test start command for new user"""
        # Mock the database to return None (new user)
        self.mock_db.get_user_zodiac.return_value = None
        
        # Call the method
        result = await self.handlers.start(mock_update, mock_context)
        
        # Verify that the database was queried with the correct user ID
        self.mock_db.get_user_zodiac.assert_called_once_with(mock_update.effective_user.id)
        
        # Verify that a reply was sent asking for zodiac sign
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message asks for zodiac sign
        assert "Какой у вас знак зодиака" in args[0]
        
        # Check that the conversation continues to ZODIAC_SIGN state
        assert result == ZODIAC_SIGN
    
    @pytest.mark.asyncio
    async def test_set_user_zodiac_valid(self, mock_update, mock_context):
        """Test setting valid zodiac sign"""
        # Set up the message text
        mock_update.message.text = "овен"
        
        # Call the method
        result = await self.handlers.set_user_zodiac(mock_update, mock_context)
        
        # Verify that the database was updated with the correct user ID and zodiac sign
        self.mock_db.add_user_settings.assert_called_once_with(mock_update.effective_user.id, "овен")
        
        # Verify that a confirmation reply was sent
        assert mock_update.message.reply_text.call_count == 2
        
        # Check that the conversation ended
        assert result == ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_set_user_zodiac_invalid(self, mock_update, mock_context):
        """Test setting invalid zodiac sign"""
        # Set up the message text
        mock_update.message.text = "invalid"
        
        # Call the method
        result = await self.handlers.set_user_zodiac(mock_update, mock_context)
        
        # Verify that the database was not updated
        self.mock_db.add_user_settings.assert_not_called()
        
        # Verify that an error reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates an error
        assert "Неверный знак зодиака" in args[0]
        
        # Check that the conversation continues in ZODIAC_SIGN state
        assert result == ZODIAC_SIGN
    
    @pytest.mark.asyncio
    async def test_add_medication(self, mock_update, mock_context):
        """Test add_medication command"""
        # Call the method
        result = await self.handlers.add_medication(mock_update, mock_context)
        
        # Verify that a reply was sent asking for medication name
        mock_update.message.reply_text.assert_called_once_with("Введите название лекарства:")
        
        # Check that the conversation continues to NAME state
        assert result == NAME
    
    @pytest.mark.asyncio
    async def test_set_name_valid(self, mock_update, mock_context):
        """Test setting valid medication name"""
        # Set up the message text
        mock_update.message.text = "Aspirin"
        
        # Call the method
        result = await self.handlers.set_name(mock_update, mock_context)
        
        # Verify that the name was stored in user_data
        assert mock_context.user_data["name"] == "Aspirin"
        
        # Verify that a reply was sent asking for dose
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message asks for dose
        assert "капсул за один прием" in args[0]
        
        # Check that the conversation continues to DOSE state
        assert result == DOSE
    
    @pytest.mark.asyncio
    async def test_set_name_empty(self, mock_update, mock_context):
        """Test setting empty medication name"""
        # Set up the message text
        mock_update.message.text = ""
        
        # Call the method
        result = await self.handlers.set_name(mock_update, mock_context)
        
        # Verify that an error reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates an error
        assert "Название не может быть пустым" in args[0]
        
        # Check that the conversation continues in NAME state
        assert result == NAME
    
    @pytest.mark.asyncio
    async def test_set_name_too_long(self, mock_update, mock_context):
        """Test setting too long medication name"""
        # Set up the message text
        mock_update.message.text = "A" * 51  # 51 characters
        
        # Call the method
        result = await self.handlers.set_name(mock_update, mock_context)
        
        # Verify that an error reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates an error
        assert "Название слишком длинное" in args[0]
        
        # Check that the conversation continues in NAME state
        assert result == NAME
    
    @pytest.mark.asyncio
    async def test_set_dose_valid(self, mock_update, mock_context):
        """Test setting valid dose"""
        # Set up the message text
        mock_update.message.text = "2"
        
        # Call the method
        result = await self.handlers.set_dose(mock_update, mock_context)
        
        # Verify that the dose was stored in user_data
        assert mock_context.user_data["dose"] == 2
        
        # Verify that a reply was sent asking for intakes
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message asks for intakes
        assert "приемов в сутки" in args[0]
        
        # Check that the conversation continues to INTAKES state
        assert result == INTAKES
    
    @pytest.mark.asyncio
    async def test_set_dose_invalid(self, mock_update, mock_context):
        """Test setting invalid dose"""
        # Set up the message text
        mock_update.message.text = "abc"
        
        # Call the method
        result = await self.handlers.set_dose(mock_update, mock_context)
        
        # Verify that an error reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates an error
        assert "Должно быть целое число" in args[0]
        
        # Check that the conversation continues in DOSE state
        assert result == DOSE
    
    @pytest.mark.asyncio
    async def test_set_intakes_valid(self, mock_update, mock_context):
        """Test setting valid intakes"""
        # Set up the message text
        mock_update.message.text = "3"
        
        # Call the method
        result = await self.handlers.set_intakes(mock_update, mock_context)
        
        # Verify that the intakes was stored in user_data
        assert mock_context.user_data["intakes"] == 3
        
        # Verify that a reply was sent asking for start date
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message asks for start date
        assert "Дата начала приема" in args[0]
        
        # Check that the conversation continues to START_DATE state
        assert result == START_DATE
    
    @pytest.mark.asyncio
    async def test_set_intakes_invalid(self, mock_update, mock_context):
        """Test setting invalid intakes"""
        # Set up the message text
        mock_update.message.text = "25"  # More than 24
        
        # Call the method
        result = await self.handlers.set_intakes(mock_update, mock_context)
        
        # Verify that an error reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates an error
        assert "Должно быть целое число от 1 до 24" in args[0]
        
        # Check that the conversation continues in INTAKES state
        assert result == INTAKES
    
    @pytest.mark.asyncio
    async def test_set_start_date_valid(self, mock_update, mock_context):
        """Test setting valid start date"""
        # Set up the message text
        mock_update.message.text = "2025-01-01"
        
        # Call the method
        result = await self.handlers.set_start_date(mock_update, mock_context)
        
        # Verify that the start date was stored in user_data
        assert mock_context.user_data["start_date"] == "2025-01-01"
        
        # Verify that a reply was sent asking for duration value
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message asks for duration value
        assert "Длительность приема" in args[0]
        
        # Check that the conversation continues to DURATION_VALUE state
        assert result == DURATION_VALUE
    
    @pytest.mark.asyncio
    async def test_set_start_date_invalid(self, mock_update, mock_context):
        """Test setting invalid start date"""
        # Set up the message text
        mock_update.message.text = "01-01-2025"  # Wrong format
        
        # Call the method
        result = await self.handlers.set_start_date(mock_update, mock_context)
        
        # Verify that an error reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates an error
        assert "Неверный формат даты" in args[0]
        
        # Check that the conversation continues in START_DATE state
        assert result == START_DATE
    
    @pytest.mark.asyncio
    async def test_set_duration_value_valid(self, mock_update, mock_context):
        """Test setting valid duration value"""
        # Set up the message text
        mock_update.message.text = "10"
        
        # Call the method
        result = await self.handlers.set_duration_value(mock_update, mock_context)
        
        # Verify that the duration value was stored in user_data
        assert mock_context.user_data["duration_value"] == 10
        
        # Verify that a reply was sent asking for duration unit
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message asks for duration unit
        assert "единицы измерения" in args[0]
        
        # Check that the conversation continues to DURATION_UNIT state
        assert result == DURATION_UNIT
    
    @pytest.mark.asyncio
    async def test_set_duration_value_invalid(self, mock_update, mock_context):
        """Test setting invalid duration value"""
        # Set up the message text
        mock_update.message.text = "0"  # Must be > 0
        
        # Call the method
        result = await self.handlers.set_duration_value(mock_update, mock_context)
        
        # Verify that an error reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates an error
        assert "Должно быть целое число больше 0" in args[0]
        
        # Check that the conversation continues in DURATION_VALUE state
        assert result == DURATION_VALUE
    
    @pytest.mark.asyncio
    async def test_set_duration_unit_valid(self, mock_update, mock_context):
        """Test setting valid duration unit"""
        # Set up the message text
        mock_update.message.text = "days"
        
        # Call the method
        result = await self.handlers.set_duration_unit(mock_update, mock_context)
        
        # Verify that the duration unit was stored in user_data
        assert mock_context.user_data["duration_unit"] == "days"
        
        # Verify that a reply was sent asking for break value
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message asks for break value
        assert "Длительность перерыва" in args[0]
        
        # Check that the conversation continues to BREAK_VALUE state
        assert result == BREAK_VALUE
    
    @pytest.mark.asyncio
    async def test_set_duration_unit_invalid(self, mock_update, mock_context):
        """Test setting invalid duration unit"""
        # Set up the message text
        mock_update.message.text = "weeks"  # Not allowed
        
        # Call the method
        result = await self.handlers.set_duration_unit(mock_update, mock_context)
        
        # Verify that an error reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates an error
        assert "Некорректный формат" in args[0]
        
        # Check that the conversation continues in DURATION_UNIT state
        assert result == DURATION_UNIT
    
    @pytest.mark.asyncio
    async def test_set_break_value_valid(self, mock_update, mock_context):
        """Test setting valid break value"""
        # Set up the message text
        mock_update.message.text = "5"
        
        # Call the method
        result = await self.handlers.set_break_value(mock_update, mock_context)
        
        # Verify that the break value was stored in user_data
        assert mock_context.user_data["break_value"] == 5
        
        # Verify that a reply was sent asking for break unit
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message asks for break unit
        assert "единицы измерения для перерыва" in args[0]
        
        # Check that the conversation continues to BREAK_UNIT state
        assert result == BREAK_UNIT
    
    @pytest.mark.asyncio
    async def test_set_break_value_invalid(self, mock_update, mock_context):
        """Test setting invalid break value"""
        # Set up the message text
        mock_update.message.text = "-1"  # Must be >= 0
        
        # Call the method
        result = await self.handlers.set_break_value(mock_update, mock_context)
        
        # Verify that an error reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates an error
        assert "Должно быть целое число 0 или больше" in args[0]
        
        # Check that the conversation continues in BREAK_VALUE state
        assert result == BREAK_VALUE
    
    @pytest.mark.asyncio
    async def test_set_break_unit_valid(self, mock_update, mock_context):
        """Test setting valid break unit"""
        # Set up the message text
        mock_update.message.text = "days"
        
        # Call the method
        result = await self.handlers.set_break_unit(mock_update, mock_context)
        
        # Verify that the break unit was stored in user_data
        assert mock_context.user_data["break_unit"] == "days"
        
        # Verify that a reply was sent asking for cycles
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message asks for cycles
        assert "Сколько всего курсов" in args[0]
        
        # Check that the conversation continues to CYCLES state
        assert result == CYCLES
    
    @pytest.mark.asyncio
    async def test_set_break_unit_invalid(self, mock_update, mock_context):
        """Test setting invalid break unit"""
        # Set up the message text
        mock_update.message.text = "weeks"  # Not allowed
        
        # Call the method
        result = await self.handlers.set_break_unit(mock_update, mock_context)
        
        # Verify that an error reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates an error
        assert "Некорректный формат" in args[0]
        
        # Check that the conversation continues in BREAK_UNIT state
        assert result == BREAK_UNIT
    
    @pytest.mark.asyncio
    async def test_set_cycles_valid(self, mock_update, mock_context):
        """Test setting valid cycles and saving medication"""
        # Set up the message text
        mock_update.message.text = "2"
        
        # Set up user_data with all required fields
        mock_context.user_data = {
            "name": "Test Med",
            "dose": 2,
            "intakes": 3,
            "start_date": "2025-01-01",
            "duration_value": 10,
            "duration_unit": "days",
            "break_value": 5,
            "break_unit": "days"
        }
        
        # Call the method
        result = await self.handlers.set_cycles(mock_update, mock_context)
        
        # Verify that the medication was added to the database
        self.mock_db.add_medication.assert_called_once()
        args, kwargs = self.mock_db.add_medication.call_args
        
        # Check that all fields were passed correctly
        assert kwargs["name"] == "Test Med"
        assert kwargs["dose_per_intake"] == 2
        assert kwargs["intakes_per_day"] == 3
        assert kwargs["start_date"] == "2025-01-01"
        assert kwargs["duration_value"] == 10
        assert kwargs["duration_unit"] == "days"
        assert kwargs["break_value"] == 5
        assert kwargs["break_unit"] == "days"
        assert kwargs["cycles"] == 2
        
        # Verify that a success reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates success
        assert "успешно добавлено" in args[0]
        
        # Check that the conversation ended
        assert result == ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_set_cycles_invalid(self, mock_update, mock_context):
        """Test setting invalid cycles"""
        # Set up the message text
        mock_update.message.text = "0"  # Must be > 0
        
        # Call the method
        result = await self.handlers.set_cycles(mock_update, mock_context)
        
        # Verify that the medication was not added to the database
        self.mock_db.add_medication.assert_not_called()
        
        # Verify that an error reply was sent
        mock_update.message.reply_text.assert_called_once()
        args, kwargs = mock_update.message.reply_text.call_args
        
        # Check that the message indicates an error
        assert "Должно быть целое число больше 0" in args[0]
        
        # Check that the conversation continues in CYCLES state
        assert result == CYCLES
    
    @pytest.mark.asyncio
    async def test_set_cycles_database_error(self, mock_update, mock_context):
        """Test database error when saving medication"""
        # Set up the message text
        mock_update.message.text = "2"
        
        # Set up user_data with all required fields
        mock_context.user_data = {
            "name": "Test Med",
            "dose": 2,
            "intakes": 3,
            "start_date": "2025-01-01",
            "duration_value": 10,
            "duration_unit": "days",
            "break_value": 5,
            "break_unit": "days"
        }
        
        # Mock the database to raise an exception
        self.mock_db.add_medication.side_effect = Exception("Database error")
        
        # Call the method
        result = await self.handlers.set_cycles(mock_update, mock_context)
        
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
    async def test_cancel(self, mock_update, mock_context):
        """Test cancel command"""
        # Call the method
        result = await self.handlers.cancel(mock_update, mock_context)
        
        # Verify that a reply was sent
        mock_update.message.reply_text.assert_called_once_with("❌ Действие отменено.")
        
        # Check that the conversation ended
        assert result == ConversationHandler.END
