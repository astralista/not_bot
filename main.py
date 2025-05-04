import os
import asyncio
from dotenv import load_dotenv

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from src.core.database import Database
from src.core.logger import logger
from src.bot.handlers.medication_handlers import MedicationHandlers, NAME, DOSE, INTAKES, START_DATE, DURATION_VALUE, DURATION_UNIT, BREAK_VALUE, BREAK_UNIT, CYCLES, EDIT_CHOICE, EDIT_FIELD
from src.bot.handlers.notification_handlers import NotificationHandlers
from src.bot.services.notification_service import NotificationService
from src.bot.services.scheduler_service import SchedulerService

def setup_handlers(application, db, logger):
    """
    Настройка обработчиков команд
    
    Args:
        application: Экземпляр приложения бота
        db (Database): Экземпляр базы данных
        logger: Логгер
    """
    # Инициализация обработчиков
    med_handlers = MedicationHandlers(db, logger)
    notif_handlers = NotificationHandlers(db, logger)
    
    # Команда /start с кнопками
    application.add_handler(CommandHandler("start", med_handlers.start))
    
    # Добавление лекарства
    add_conv = ConversationHandler(
        entry_points=[CommandHandler("add", med_handlers.add_medication)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, med_handlers.set_name)],
            DOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, med_handlers.set_dose)],
            INTAKES: [MessageHandler(filters.TEXT & ~filters.COMMAND, med_handlers.set_intakes)],
            START_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, med_handlers.set_start_date)],
            DURATION_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, med_handlers.set_duration_value)],
            DURATION_UNIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, med_handlers.set_duration_unit)],
            BREAK_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, med_handlers.set_break_value)],
            BREAK_UNIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, med_handlers.set_break_unit)],
            CYCLES: [MessageHandler(filters.TEXT & ~filters.COMMAND, med_handlers.set_cycles)],
        },
        fallbacks=[CommandHandler("cancel", med_handlers.cancel)],
    )
    application.add_handler(add_conv)
    
    # Редактирование лекарства
    edit_conv = ConversationHandler(
        entry_points=[CommandHandler("edit", med_handlers.edit_medication)],
        states={
            EDIT_CHOICE: [CallbackQueryHandler(med_handlers.edit_choice)],
            EDIT_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, med_handlers.save_edit)],
        },
        fallbacks=[CommandHandler("cancel", med_handlers.cancel)],
        allow_reentry=True
    )
    application.add_handler(edit_conv)
    
    # Просмотр списка лекарств
    application.add_handler(CommandHandler("list", med_handlers.list_medications))
    
    # Удаление лекарства
    application.add_handler(CommandHandler("delete", med_handlers.delete_medication))
    application.add_handler(CallbackQueryHandler(med_handlers.delete_confirm, pattern="^delete_"))
    
    # Обработка выбора поля для редактирования
    application.add_handler(
        CallbackQueryHandler(
            med_handlers.handle_field_selection,
            pattern="^(name|dose|intakes|start_date|duration_value|duration_unit|break_value|break_unit|cycles)$"
        )
    )
    
    # Установка знака зодиака
    application.add_handler(CommandHandler("set_zodiac", notif_handlers.set_zodiac))
    
    # Управление уведомлениями
    application.add_handler(CommandHandler("notifications", notif_handlers.toggle_notifications))
    application.add_handler(CommandHandler("set_time", notif_handlers.set_notification_time))

def setup_services(application, db):
    """
    Настройка сервисов
    
    Args:
        application: Экземпляр приложения бота
        db (Database): Экземпляр базы данных
    
    Returns:
        tuple: Экземпляры сервисов (notification_service, scheduler_service)
    """
    # Инициализация сервисов
    notification_service = NotificationService(db, application)
    scheduler_service = SchedulerService(db, application)
    
    # Настройка и запуск сервисов
    notification_service.setup_daily_notifications()
    notification_service.start()
    
    scheduler_service.setup_medication_checks()
    scheduler_service.start()
    
    return notification_service, scheduler_service

async def main():
    """
    Основная функция запуска бота
    """
    # Загрузка переменных окружения
    load_dotenv()
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("Токен бота не найден!")
    
    # Инициализация базы данных
    db = Database("data/users.db")
    
    # Инициализация приложения
    application = Application.builder().token(TOKEN).build()
    
    # Настройка обработчиков и сервисов
    setup_handlers(application, db, logger)
    notification_service, scheduler_service = setup_services(application, db)
    
    # Запуск бота
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    try:
        # Бесконечный цикл для поддержания работы бота
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        # Корректное завершение работы
        await application.stop()
        await application.updater.stop()

if __name__ == "__main__":
    asyncio.run(main())
