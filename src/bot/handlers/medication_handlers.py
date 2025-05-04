import re
import logging
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from ...core.database import Database
from ...utils.validators import validate_date, validate_number, validate_unit, validate_zodiac_sign
from ...utils.helpers import format_medication_info

# Состояния для ConversationHandler
(
    NAME, DOSE, INTAKES, START_DATE,
    DURATION_VALUE, DURATION_UNIT,
    BREAK_VALUE, BREAK_UNIT, CYCLES,
    EDIT_CHOICE, EDIT_FIELD,
    ZODIAC_SIGN
) = range(12)


class MedicationHandlers:
    """
    Обработчики команд для управления лекарствами
    """
    def __init__(self, db: Database, logger):
        """
        Инициализация обработчиков
        
        Args:
            db (Database): Экземпляр базы данных
            logger: Логгер
        """
        self.db = db
        self.logger = logger.getChild('MedicationHandlers')
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /start
        
        Args:
            update (Update): Объект обновления
            context (ContextTypes.DEFAULT_TYPE): Контекст
            
        Returns:
            int: Следующее состояние разговора или None
        """
        user_id = update.effective_user.id
        zodiac_sign = self.db.get_user_zodiac(user_id)
        
        if zodiac_sign:
            # Если пользователь уже есть в базе, показываем обычное меню
            keyboard = [["/add", "/list"], ["/edit", "/delete"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(
                "💊 Бот-напоминатель о лекарствах\n\n"
                "Выберите действие:",
                reply_markup=reply_markup
            )
            return ConversationHandler.END
        else:
            # Если пользователя нет в базе, начинаем знакомство
            await update.message.reply_text(
                "👋 Привет! Я бот-напоминатель о лекарствах.\n\n"
                "Давайте познакомимся! Какой у вас знак зодиака?\n\n"
                "Доступные знаки: овен, телец, близнецы, рак, лев, дева, "
                "весы, скорпион, стрелец, козерог, водолей, рыбы"
            )
            return ZODIAC_SIGN
            
    async def set_user_zodiac(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработка ввода знака зодиака при первом запуске
        
        Args:
            update (Update): Объект обновления
            context (ContextTypes.DEFAULT_TYPE): Контекст
        
        Returns:
            int: Следующее состояние разговора
        """
        zodiac_input = update.message.text.strip().lower()
        
        if not validate_zodiac_sign(zodiac_input):
            await update.message.reply_text(
                "❌ Неверный знак зодиака!\n\n"
                "Доступные знаки: овен, телец, близнецы, рак, лев, дева, "
                "весы, скорпион, стрелец, козерог, водолей, рыбы\n\n"
                "Пожалуйста, введите ваш знак зодиака:"
            )
            return ZODIAC_SIGN
        
        try:
            user_id = update.effective_user.id
            self.db.add_user_settings(user_id, zodiac_input)
            
            await update.message.reply_text(
                f"♌ Отлично! Ваш знак зодиака: {zodiac_input.capitalize()}\n\n"
                f"Теперь вы будете получать персональный гороскоп!"
            )
            
            # Показываем основное меню
            keyboard = [["/add", "/list"], ["/edit", "/delete"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(
                "💊 Бот-напоминатель о лекарствах\n\n"
                "Выберите действие:",
                reply_markup=reply_markup
            )
            return ConversationHandler.END
            
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении знака зодиака: {e}")
            await update.message.reply_text("❌ Произошла ошибка при сохранении. Попробуйте позже.")
            return ConversationHandler.END
    
    # Методы для добавления лекарств
    async def add_medication(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Начало добавления лекарства
        
        Args:
            update (Update): Объект обновления
            context (ContextTypes.DEFAULT_TYPE): Контекст
        
        Returns:
            int: Следующее состояние разговора
        """
        await update.message.reply_text("Введите название лекарства:")
        return NAME
    
    async def set_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Установка названия лекарства
        
        Args:
            update (Update): Объект обновления
            context (ContextTypes.DEFAULT_TYPE): Контекст
        
        Returns:
            int: Следующее состояние разговора
        """
        name = update.message.text.strip()
        if not name:
            await update.message.reply_text("❌ Название не может быть пустым. Введите название:")
            return NAME
        if len(name) > 50:
            await update.message.reply_text("❌ Название слишком длинное (макс. 50 символов). Введите снова:")
            return NAME

        context.user_data["name"] = name
        await update.message.reply_text("💊 Сколько капсул за один прием? (Только число):")
        return DOSE
    
    async def set_dose(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Установка дозы лекарства
        
        Args:
            update (Update): Объект обновления
            context (ContextTypes.DEFAULT_TYPE): Контекст
        
        Returns:
            int: Следующее состояние разговора
        """
        if not validate_number(update.message.text):
            await update.message.reply_text("❌ Должно быть целое число больше 0. Введите количество капсул:")
            return DOSE

        context.user_data["dose"] = int(update.message.text)
        await update.message.reply_text("⏱ Сколько приемов в сутки? (Только число):")
        return INTAKES
    
    async def set_intakes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Установка количества приемов в день
        
        Args:
            update (Update): Объект обновления
            context (ContextTypes.DEFAULT_TYPE): Контекст
        
        Returns:
            int: Следующее состояние разговора
        """
        if not validate_number(update.message.text, 1, 24):
            await update.message.reply_text("❌ Должно быть целое число от 1 до 24. Введите снова:")
            return INTAKES

        context.user_data["intakes"] = int(update.message.text)
        await update.message.reply_text("📅 Дата начала приема (в формате ГГГГ-ММ-ДД):")
        return START_DATE
    
    async def set_start_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Установка даты начала приема
        
        Args:
            update (Update): Объект обновления
            context (ContextTypes.DEFAULT_TYPE): Контекст
        
        Returns:
            int: Следующее состояние разговора
        """
        if not validate_date(update.message.text):
            await update.message.reply_text("❌ Неверный формат даты. Введите в формате ГГГГ-ММ-ДД:")
            return START_DATE

        context.user_data["start_date"] = update.message.text
        await update.message.reply_text("⏳ Длительность приема (число дней/месяцев):")
        return DURATION_VALUE
    
    async def set_duration_value(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Установка значения длительности приема
        
        Args:
            update (Update): Объект обновления
            context (ContextTypes.DEFAULT_TYPE): Контекст
        
        Returns:
            int: Следующее состояние разговора
        """
        if not validate_number(update.message.text, 1):
            await update.message.reply_text("❌ Должно быть целое число больше 0. Введите снова:")
            return DURATION_VALUE

        context.user_data["duration_value"] = int(update.message.text)
        await update.message.reply_text("Выберите единицы измерения (напишите 'days' или 'months'):")
        return DURATION_UNIT
    
    async def set_duration_unit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Установка единицы измерения длительности
        
        Args:
            update (Update): Объект обновления
            context (ContextTypes.DEFAULT_TYPE): Контекст
        
        Returns:
            int: Следующее состояние разговора
        """
        if not validate_unit(update.message.text):
            await update.message.reply_text("❌ Некорректный формат. Введите 'days' или 'months':")
            return DURATION_UNIT

        context.user_data["duration_unit"] = update.message.text.lower()
        await update.message.reply_text("⏸ Длительность перерыва между курсами (число дней/месяцев):")
        return BREAK_VALUE
    
    async def set_break_value(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Установка значения длительности перерыва
        
        Args:
            update (Update): Объект обновления
            context (ContextTypes.DEFAULT_TYPE): Контекст
        
        Returns:
            int: Следующее состояние разговора
        """
        if not validate_number(update.message.text, 0):
            await update.message.reply_text("❌ Должно быть целое число 0 или больше. Введите снова:")
            return BREAK_VALUE

        context.user_data["break_value"] = int(update.message.text)
        await update.message.reply_text("Выберите единицы измерения для перерыва (напишите 'days' или 'months'):")
        return BREAK_UNIT
    
    async def set_break_unit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Установка единицы измерения перерыва
        
        Args:
            update (Update): Объект обновления
            context (ContextTypes.DEFAULT_TYPE): Контекст
        
        Returns:
            int: Следующее состояние разговора
        """
        if not validate_unit(update.message.text):
            await update.message.reply_text("❌ Некорректный формат. Введите 'days' или 'months':")
            return BREAK_UNIT

        context.user_data["break_unit"] = update.message.text.lower()
        await update.message.reply_text("♻️ Сколько всего курсов? (Введите число, 1 если один курс):")
        return CYCLES
    
    async def set_cycles(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Установка количества курсов и сохранение лекарства
        
        Args:
            update (Update): Объект обновления
            context (ContextTypes.DEFAULT_TYPE): Контекст
        
        Returns:
            int: Следующее состояние разговора
        """
        if not validate_number(update.message.text, 1):
            await update.message.reply_text("❌ Должно быть целое число больше 0. Введите снова:")
            return CYCLES

        try:
            user_data = context.user_data
            self.db.add_medication(
                user_id=update.message.from_user.id,
                name=user_data["name"],
                dose_per_intake=user_data["dose"],
                intakes_per_day=user_data["intakes"],
                start_date=user_data["start_date"],
                duration_value=user_data["duration_value"],
                duration_unit=user_data["duration_unit"],
                break_value=user_data["break_value"],
                break_unit=user_data["break_unit"],
                cycles=int(update.message.text),
            )
            await update.message.reply_text("✅ Лекарство успешно добавлено!")
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении: {e}")
            await update.message.reply_text("❌ Произошла ошибка при сохранении. Попробуйте снова.")

        return ConversationHandler.END
    
    # Методы для редактирования лекарств
    async def edit_medication(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Начало редактирования лекарства
        
        Args:
            update (Update): Объект обновления
            context (ContextTypes.DEFAULT_TYPE): Контекст
        
        Returns:
            int: Следующее состояние разговора
        """
        self.logger.info(f"Начало команды /edit от пользователя {update.effective_user.id}")

        # Очищаем предыдущие данные
        context.user_data.pop("edit_id", None)
        context.user_data.pop("edit_field", None)

        meds = self.db.get_medications(update.effective_user.id)
        self.logger.info(f"Найдено лекарств: {len(meds)}")

        if not meds:
            self.logger.warning("Нет лекарств для редактирования")
            await update.message.reply_text("ℹ️ Нет лекарств для редактирования.")
            return ConversationHandler.END

        keyboard = [
            [InlineKeyboardButton(f"{med[2]} (ID: {med[0]})", callback_data=f"edit_{med[0]}")]
            for med in meds
        ]

        self.logger.info("Отправка списка лекарств для выбора")
        await update.message.reply_text(
            "Выберите лекарство для редактирования:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return EDIT_CHOICE
    
    async def edit_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработка выбора лекарства для редактирования
        
        Args:
            update (Update): Объект обновления
            context (ContextTypes.DEFAULT_TYPE): Контекст
        
        Returns:
            int: Следующее состояние разговора
        """
        query = update.callback_query
        await query.answer()

        self.logger.info(f"Получен callback: {query.data}")

        if query.data.startswith("edit_"):
            med_id = int(query.data.split("_")[1])
            self.logger.info(f"Выбрано лекарство ID: {med_id}")

            # Проверяем существование лекарства
            med = self.db.get_medication_by_id(med_id)
            if not med:
                self.logger.error(f"Лекарство {med_id} не найдено в БД")
                await query.edit_message_text("❌ Лекарство не найдено")
                return ConversationHandler.END

            context.user_data["edit_id"] = med_id

            self.logger.info("Создаем клавиатуру для выбора поля")
            keyboard = [
                [InlineKeyboardButton("Название", callback_data="name")],
                [InlineKeyboardButton("Дозу", callback_data="dose")],
                [InlineKeyboardButton("Приемов в день", callback_data="intakes")],
                [InlineKeyboardButton("Дату начала", callback_data="start_date")],
                [InlineKeyboardButton("Длительность", callback_data="duration_value")],
                [InlineKeyboardButton("Единицы длительности", callback_data="duration_unit")],
                [InlineKeyboardButton("Перерыв", callback_data="break_value")],
                [InlineKeyboardButton("Единицы перерыва", callback_data="break_unit")],
                [InlineKeyboardButton("Курсы", callback_data="cycles")],
            ]

            try:
                self.logger.info("Пытаемся отредактировать сообщение")
                await query.edit_message_text(
                    "Что именно хотите изменить?",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                self.logger.info("Сообщение успешно отредактировано")
                return EDIT_FIELD
            except Exception as e:
                self.logger.error(f"Ошибка при редактировании сообщения: {str(e)}")
                return ConversationHandler.END
    
    async def handle_field_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработка выбора поля для редактирования
        
        Args:
            update (Update): Объект обновления
            context (ContextTypes.DEFAULT_TYPE): Контекст
        
        Returns:
            int: Следующее состояние разговора
        """
        query = update.callback_query
        await query.answer()

        field = query.data
        self.logger.info(f"Выбрано поле для редактирования: {field}")

        # Сохраняем выбранное поле в контексте
        context.user_data["edit_field"] = field

        # Запрашиваем новое значение
        field_names = {
            "name": "название",
            "dose": "дозу (число)",
            "intakes": "количество приемов в день (число)",
            "start_date": "дату начала (ГГГГ-ММ-ДД)",
            "duration_value": "длительность (число)",
            "duration_unit": "единицы длительности (days/months)",
            "break_value": "длительность перерыва (число)",
            "break_unit": "единицы перерыва (days/months)",
            "cycles": "количество курсов (число)"
        }

        await query.edit_message_text(
            f"Введите новое значение для {field_names[field]}:"
        )
        return EDIT_FIELD
    
    async def save_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Сохранение отредактированного поля
        
        Args:
            update (Update): Объект обновления
            context (ContextTypes.DEFAULT_TYPE): Контекст
        
        Returns:
            int: Следующее состояние разговора
        """
        self.logger.info(f"Начало сохранения. Контекст: {context.user_data}")
        self.logger.info("Начало обработки выбранного поля")

        user_id = update.effective_user.id
        self.logger.info(f"Начало сохранения редактирования для user_id={user_id}")

        if "edit_id" not in context.user_data or "edit_field" not in context.user_data:
            self.logger.error("Нет данных для редактирования в context.user_data")
            await update.message.reply_text("❌ Сессия редактирования устарела. Начните заново.")
            return ConversationHandler.END

        self.logger.info(f"Данные контекста: {context.user_data}")

        med_id = context.user_data["edit_id"]
        field = context.user_data["edit_field"]
        new_value = update.message.text.strip()

        self.logger.info(f"Попытка изменить medication_id={med_id}, поле={field}, значение='{new_value}'")

        try:
            # Проверяем существование записи
            med = self.db.get_medication_by_id(med_id)
            if not med:
                self.logger.error(f"Лекарство {med_id} не найдено")
                await update.message.reply_text("❌ Лекарство не найдено в базе данных")
                return ConversationHandler.END

            self.logger.debug(f"Текущие данные лекарства: {med}")

            # Валидация
            if field == "name":
                if len(new_value) > 50:
                    error_msg = "Название слишком длинное (макс. 50 символов)"
                    self.logger.warning(error_msg)
                    await update.message.reply_text(f"❌ {error_msg}")
                    return EDIT_FIELD

            elif field in ["dose", "intakes", "duration_value", "break_value", "cycles"]:
                if not new_value.isdigit():
                    error_msg = "Должно быть целое число"
                    self.logger.warning(error_msg)
                    await update.message.reply_text(f"❌ {error_msg}")
                    return EDIT_FIELD
                if int(new_value) <= 0:
                    error_msg = "Число должно быть больше 0"
                    self.logger.warning(error_msg)
                    await update.message.reply_text(f"❌ {error_msg}")
                    return EDIT_FIELD

            elif field in ["duration_unit", "break_unit"]:
                if new_value.lower() not in ["days", "months"]:
                    error_msg = "Допустимые значения: 'days' или 'months'"
                    self.logger.warning(error_msg)
                    await update.message.reply_text(f"❌ {error_msg}")
                    return EDIT_FIELD

            elif field == "start_date":
                if not validate_date(new_value):
                    error_msg = "Неверный формат даты (требуется ГГГГ-ММ-ДД)"
                    self.logger.warning(error_msg)
                    await update.message.reply_text(f"❌ {error_msg}")
                    return EDIT_FIELD

            # Преобразуем тип
            update_value = int(new_value) if field in ["dose", "intakes", "duration_value", "break_value",
                                                     "cycles"] else new_value
            self.logger.info(f"Подготовлено значение для обновления: {update_value} ({type(update_value)})")

            # Обновляем в БД
            self.logger.info(f"Попытка обновления БД...")
            self.db.update_medication(med_id, **{field: update_value})

            # Проверяем обновление
            updated_med = self.db.get_medication_by_id(med_id)
            if not updated_med:
                self.logger.error("Не удалось получить обновленные данные")
                await update.message.reply_text("❌ Не удалось подтвердить изменение")
            else:
                self.logger.info(f"Успешно обновлено. Новые данные: {updated_med}")
                await update.message.reply_text(f"✅ Поле '{field}' успешно обновлено!")

        except Exception as e:
            self.logger.error(f"Ошибка при сохранении: {str(e)}", exc_info=True)
            await update.message.reply_text("❌ Произошла ошибка при сохранении. Попробуйте снова.")

        finally:
            # Очищаем сессию
            context.user_data.pop("edit_id", None)
            context.user_data.pop("edit_field", None)
            self.logger.info("Сессия редактирования очищена")

        return ConversationHandler.END
    
    # Методы для удаления лекарств
    async def delete_medication(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Начало удаления лекарства
        
        Args:
            update (Update): Объект обновления
            context (ContextTypes.DEFAULT_TYPE): Контекст
        """
        meds = self.db.get_medications(update.message.from_user.id)
        if not meds:
            await update.message.reply_text("ℹ️ Нет лекарств для удаления.")
            return

        keyboard = [
            [InlineKeyboardButton(f"{med[2]} (ID: {med[0]})", callback_data=f"delete_{med[0]}")]
            for med in meds
        ]
        await update.message.reply_text(
            "Выберите лекарство для удаления:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def delete_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Подтверждение удаления лекарства
        
        Args:
            update (Update): Объект обновления
            context (ContextTypes.DEFAULT_TYPE): Контекст
        """
        query = update.callback_query
        await query.answer()
        med_id = int(query.data.split("_")[1])
        self.db.delete_medication(med_id)
        await query.edit_message_text("✅ Лекарство удалено!")
    
    # Метод для просмотра списка лекарств
    async def list_medications(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Просмотр списка лекарств
        
        Args:
            update (Update): Объект обновления
            context (ContextTypes.DEFAULT_TYPE): Контекст
        """
        try:
            meds = self.db.get_medications(update.message.from_user.id)
            if not meds:
                await update.message.reply_text("ℹ️ У вас пока нет добавленных лекарств.")
                return

            text = "💊 Ваши лекарства:\n\n"
            current_date = datetime.now().date()

            for med in meds:
                try:
                    text += format_medication_info(med) + "\n\n"
                except Exception as e:
                    self.logger.error(f"Ошибка обработки лекарства ID {med[0]}: {e}")
                    text += f"⚠️ Лекарство ID {med[0]} - ошибка данных\n\n"

            await update.message.reply_text(text, parse_mode="HTML")

        except Exception as e:
            self.logger.error(f"Ошибка при получении списка: {e}")
            await update.message.reply_text("❌ Произошла ошибка при загрузке данных. Попробуйте позже.")
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Отмена текущего действия
        
        Args:
            update (Update): Объект обновления
            context (ContextTypes.DEFAULT_TYPE): Контекст
        
        Returns:
            int: Следующее состояние разговора
        """
        await update.message.reply_text("❌ Действие отменено.")
        return ConversationHandler.END
