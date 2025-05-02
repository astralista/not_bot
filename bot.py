import os
import asyncio
import re
import logging
from datetime import datetime, timedelta
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from database import Database
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from logger_config import logger

# Состояния для ConversationHandler
(
    NAME, DOSE, INTAKES, START_DATE,
    DURATION_VALUE, DURATION_UNIT,
    BREAK_VALUE, BREAK_UNIT, CYCLES,
    EDIT_CHOICE, EDIT_FIELD
) = range(11)


class MedicationBot:
    def __init__(self, token: str):
        self.logger = logger.getChild('MedicationBot')
        self.token = token
        self.db = Database("data/users.db")
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()
        self.setup_scheduler()

    # Вспомогательные методы валидации
    async def validate_date(self, date_str: str) -> bool:
        """Проверка формата даты (ГГГГ-ММ-ДД)"""
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return False
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    async def validate_number(self, text: str, min_val: int = 1, max_val: int = None) -> bool:
        """Проверка что текст - число в диапазоне"""
        if not text.isdigit():
            return False
        num = int(text)
        if num < min_val:
            return False
        if max_val is not None and num > max_val:
            return False
        return True

    async def validate_unit(self, text: str) -> bool:
        """Проверка допустимых значений (days/months)"""
        return text.lower() in ['days', 'months']

    def setup_handlers(self):
        # Команда /start с кнопками
        self.application.add_handler(CommandHandler("start", self.start))

        # Добавление лекарства
        add_conv = ConversationHandler(
            entry_points=[CommandHandler("add", self.add_medication)],
            states={
                NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_name)],
                DOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_dose)],
                INTAKES: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_intakes)],
                START_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_start_date)],
                DURATION_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_duration_value)],
                DURATION_UNIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_duration_unit)],
                BREAK_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_break_value)],
                BREAK_UNIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_break_unit)],
                CYCLES: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_cycles)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )
        self.application.add_handler(add_conv)

        # Редактирование лекарства
        edit_conv = ConversationHandler(
            entry_points=[CommandHandler("edit", self.edit_medication)],
            states={
                EDIT_CHOICE: [CallbackQueryHandler(self.edit_choice)],
                EDIT_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_edit)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            allow_reentry=True  # Добавляем эту строку
        )
        self.application.add_handler(edit_conv)

        # Просмотр списка лекарств
        self.application.add_handler(CommandHandler("list", self.list_medications))

        # Удаление лекарства
        self.application.add_handler(CommandHandler("delete", self.delete_medication))
        self.application.add_handler(CallbackQueryHandler(self.delete_confirm, pattern="^delete_"))

        # Обработка /edit
        self.application.add_handler(
            CallbackQueryHandler(
                self.handle_field_selection,
                pattern="^(name|dose|intakes|start_date|duration_value|duration_unit|break_value|break_unit|cycles)$"
            )
        )

    def setup_scheduler(self):
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            self.send_daily_notifications,
            'cron',
            hour=9,
            minute=0,
            timezone='Europe/Moscow'
        )
        scheduler.start()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [["/add", "/list"], ["/edit", "/delete"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "💊 Бот-напоминатель о лекарствах\n\n"
            "Выберите действие:",
            reply_markup=reply_markup
        )

    # Методы для добавления лекарств с валидацией
    async def add_medication(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Введите название лекарства:")
        return NAME

    async def set_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        if not await self.validate_number(update.message.text):
            await update.message.reply_text("❌ Должно быть целое число больше 0. Введите количество капсул:")
            return DOSE

        context.user_data["dose"] = int(update.message.text)
        await update.message.reply_text("⏱ Сколько приемов в сутки? (Только число):")
        return INTAKES

    async def set_intakes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.validate_number(update.message.text, 1):
            await update.message.reply_text("❌ Должно быть целое число от 1 до 24. Введите снова:")
            return INTAKES

        intakes = int(update.message.text)
        if intakes > 24:
            await update.message.reply_text("❌ Не более 24 приемов в сутки. Введите снова:")
            return INTAKES

        context.user_data["intakes"] = intakes
        await update.message.reply_text("📅 Дата начала приема (в формате ГГГГ-ММ-ДД):")
        return START_DATE

    async def set_start_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.validate_date(update.message.text):
            await update.message.reply_text("❌ Неверный формат даты. Введите в формате ГГГГ-ММ-ДД:")
            return START_DATE

        context.user_data["start_date"] = update.message.text
        await update.message.reply_text("⏳ Длительность приема (число дней/месяцев):")
        return DURATION_VALUE

    async def set_duration_value(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.validate_number(update.message.text, 1):
            await update.message.reply_text("❌ Должно быть целое число больше 0. Введите снова:")
            return DURATION_VALUE

        context.user_data["duration_value"] = int(update.message.text)
        await update.message.reply_text("Выберите единицы измерения (напишите 'days' или 'months'):")
        return DURATION_UNIT

    async def set_duration_unit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.validate_unit(update.message.text):
            await update.message.reply_text("❌ Некорректный формат. Введите 'days' или 'months':")
            return DURATION_UNIT

        context.user_data["duration_unit"] = update.message.text.lower()
        await update.message.reply_text("⏸ Длительность перерыва между курсами (число дней/месяцев):")
        return BREAK_VALUE

    async def set_break_value(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.validate_number(update.message.text, 0):
            await update.message.reply_text("❌ Должно быть целое число 0 или больше. Введите снова:")
            return BREAK_VALUE

        context.user_data["break_value"] = int(update.message.text)
        await update.message.reply_text("Выберите единицы измерения для перерыва (напишите 'days' или 'months'):")
        return BREAK_UNIT

    async def set_break_unit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.validate_unit(update.message.text):
            await update.message.reply_text("❌ Некорректный формат. Введите 'days' или 'months':")
            return BREAK_UNIT

        context.user_data["break_unit"] = update.message.text.lower()
        await update.message.reply_text("♻️ Сколько всего курсов? (Введите число, 1 если один курс):")
        return CYCLES

    async def set_cycles(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.validate_number(update.message.text, 1):
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

    # Методы для редактирования
    # метод для обработки выбора поля
    async def handle_field_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    async def edit_medication(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    async def save_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                if not await self.validate_date(new_value):
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

    # Методы для удаления
    async def delete_medication(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        query = update.callback_query
        await query.answer()
        med_id = int(query.data.split("_")[1])
        self.db.delete_medication(med_id)
        await query.edit_message_text("✅ Лекарство удалено!")

    # Метод для просмотра списка с защитой от ошибок
    async def list_medications(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            meds = self.db.get_medications(update.message.from_user.id)
            if not meds:
                await update.message.reply_text("ℹ️ У вас пока нет добавленных лекарств.")
                return

            text = "💊 Ваши лекарства:\n\n"
            current_date = datetime.now().date()

            for med in meds:
                try:
                    # Безопасный парсинг данных
                    med_id, _, name, dose, intakes, start_date_str, duration_val, duration_unit, break_val, break_unit, cycles = med

                    # Проверка и парсинг даты
                    if not start_date_str:
                        text += f"⚠️ {name} - отсутствует дата начала\n"
                        continue

                    try:
                        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                    except ValueError:
                        text += f"⚠️ {name} - некорректная дата начала\n"
                        continue

                    # Расчет дней
                    duration_days = duration_val if duration_unit == "days" else duration_val * 30
                    end_date = start_date + timedelta(days=duration_days)
                    days_left = (end_date - current_date).days

                    text += (
                        f"• <b>{name}</b> (ID: {med_id})\n"
                        f"  🟢 {dose} капс. × {intakes} р/день\n"
                        f"  📅 Начало: {start_date_str}\n"
                    )

                    if days_left > 0:
                        text += f"  ⏳ Осталось: {days_left} дней\n\n"
                    else:
                        break_days = break_val if break_unit == "days" else break_val * 30
                        next_cycle = end_date + timedelta(days=break_days)
                        text += f"  ⏸️ Перерыв до {next_cycle.strftime('%d.%m.%Y')}\n\n"

                except Exception as e:
                    self.logger.error(f"Ошибка обработки лекарства ID {med[0]}: {e}")
                    text += f"⚠️ Лекарство ID {med[0]} - ошибка данных\n\n"

            await update.message.reply_text(text, parse_mode="HTML")

        except Exception as e:
            self.logger.error(f"Ошибка при получении списка: {e}")
            await update.message.reply_text("❌ Произошла ошибка при загрузке данных. Попробуйте позже.")

    # Метод для ежедневных уведомлений
    async def send_daily_notifications(self):
        try:
            all_meds = self.db.get_all_medications()
            if not all_meds:
                return

            current_date = datetime.now().date()

            for user_id in set(med[1] for med in all_meds):
                user_meds = [m for m in all_meds if m[1] == user_id]
                message = "💊 Лекарства на сегодня:\n\n"

                for med in user_meds:
                    try:
                        # Безопасная обработка данных
                        _, _, name, dose, intakes, start_date_str, duration_val, duration_unit, break_val, break_unit, cycles = med

                        if not start_date_str:
                            continue

                        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                        duration_days = duration_val if duration_unit == "days" else duration_val * 30
                        end_date = start_date + timedelta(days=duration_days)
                        days_left = (end_date - current_date).days

                        if days_left > 0:
                            message += (
                                f"• <b>{name}</b>\n"
                                f"  {dose} капс. × {intakes} р/день\n"
                                f"  📅 Осталось: {days_left} дней\n\n"
                            )
                        else:
                            break_days = break_val if break_unit == "days" else break_val * 30
                            next_cycle = end_date + timedelta(days=break_days)
                            message += (
                                f"• <b>{name}</b>\n"
                                f"  ⏸️ Перерыв до {next_cycle.strftime('%d.%m.%Y')}\n\n"
                            )

                    except Exception as e:
                        self.logger.error(f"Ошибка обработки лекарства для уведомления: {e}")
                        continue

                if len(message) > 10:  # Если есть что отправлять
                    try:
                        await self.application.bot.send_message(user_id, message, parse_mode="HTML")
                    except Exception as e:
                        self.logger.error(f"Не удалось отправить уведомление пользователю {user_id}: {e}")

        except Exception as e:
            self.logger.error(f"Ошибка в ежедневных уведомлениях: {e}")

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("❌ Действие отменено.")
        return ConversationHandler.END

    def run(self):
        self.application.run_polling()
