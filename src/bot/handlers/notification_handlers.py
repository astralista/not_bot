import logging
from telegram import Update
from telegram.ext import ContextTypes

from ...core.database import Database
from ...utils.validators import validate_zodiac_sign


class NotificationHandlers:
    """
    Обработчики команд для управления уведомлениями
    """
    def __init__(self, db: Database, logger):
        """
        Инициализация обработчиков
        
        Args:
            db (Database): Экземпляр базы данных
            logger: Логгер
        """
        self.db = db
        self.logger = logger.getChild('NotificationHandlers')
    
    async def set_zodiac(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /set_zodiac
        
        Args:
            update (Update): Объект обновления
            context (ContextTypes.DEFAULT_TYPE): Контекст
        """
        if not context.args:
            await update.message.reply_text(
                "Укажите ваш знак зодиака после команды:\n"
                "/set_zodiac овен\n"
                "Доступные знаки: овен, телец, близнецы, рак, лев, дева, "
                "весы, скорпион, стрелец, козерог, водолей, рыбы"
            )
            return

        sign = ' '.join(context.args).lower()
        
        if not validate_zodiac_sign(sign):
            await update.message.reply_text("Неверный знак зодиака!")
            return

        try:
            self.db.add_user_settings(update.effective_user.id, sign)
            await update.message.reply_text(
                f"♌ Ваш знак зодиака сохранён: {sign.capitalize()}\n"
                f"Теперь вы будете получать персональный гороскоп!"
            )
        except Exception as e:
            self.logger.error(f"Error saving zodiac: {e}")
            await update.message.reply_text("Произошла ошибка при сохранении.")
    
    async def toggle_notifications(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /notifications для включения/выключения уведомлений
        
        Args:
            update (Update): Объект обновления
            context (ContextTypes.DEFAULT_TYPE): Контекст
        """
        # Здесь будет логика включения/выключения уведомлений
        # Пока заглушка
        await update.message.reply_text(
            "🔔 Уведомления включены!\n"
            "Вы будете получать напоминания о приеме лекарств и ежедневную сводку."
        )
    
    async def set_notification_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /set_time для установки времени ежедневных уведомлений
        
        Args:
            update (Update): Объект обновления
            context (ContextTypes.DEFAULT_TYPE): Контекст
        """
        # Здесь будет логика установки времени уведомлений
        # Пока заглушка
        await update.message.reply_text(
            "⏰ Время ежедневных уведомлений установлено на 9:00."
        )
