from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from ...core.database import Database
from ...utils.helpers import calculate_next_notification

class NotificationService:
    """
    Сервис для отправки уведомлений пользователям
    """
    def __init__(self, db: Database, bot_application):
        """
        Инициализация сервиса уведомлений
        
        Args:
            db (Database): Экземпляр базы данных
            bot_application: Экземпляр приложения бота
        """
        self.db = db
        self.app = bot_application
        self.scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    
    def start(self):
        """
        Запуск планировщика уведомлений
        """
        self.scheduler.start()
    
    def setup_daily_notifications(self):
        """
        Настройка ежедневных утренних уведомлений
        """
        for user_id in self.db.get_all_users():
            self.scheduler.add_job(
                self.send_daily_notification,
                'cron',
                hour=9,
                minute=0,
                args=[user_id],
                id=f"daily_{user_id}"
            )
    
    async def send_daily_notification(self, user_id: int):
        """
        Отправка ежедневного утреннего уведомления
        
        Args:
            user_id (int): ID пользователя
        """
        try:
            from ...utils.services import Services
            
            sign = self.db.get_user_zodiac(user_id) or "овен"  # Значение по умолчанию
            
            message = (
                "🌅 Доброе утро!\n\n" +
                Services.get_weather("Moscow") + "\n\n" +
                Services.get_weather("Brest,BY") + "\n\n" +
                Services.get_exchange_rates() + "\n\n" +
                Services.get_horoscope(sign) + "\n\n" +
                Services.get_daily_quote()
            )
            
            await self._send_message(user_id, message)
        except Exception as e:
            self.app.logger.error(f"Ошибка отправки ежедневного уведомления: {e}")
    
    async def send_medication_reminder(self, user_id: int, med_name: str, dose: int):
        """
        Напоминание о приеме лекарства
        
        Args:
            user_id (int): ID пользователя
            med_name (str): Название лекарства
            dose (int): Доза приема
        """
        message = f"💊 Напоминание: примите {dose} капсул(ы) {med_name}"
        await self._send_message(user_id, message)
    
    async def send_medications_list(self, user_id: int):
        """
        Отправка списка лекарств пользователю
        
        Args:
            user_id (int): ID пользователя
        """
        try:
            meds = self.db.get_medications(user_id)
            if not meds:
                await self._send_message(user_id, "ℹ️ У вас пока нет добавленных лекарств.")
                return
            
            from ...utils.helpers import format_medication_info
            
            text = "💊 Ваши лекарства:\n\n"
            for med in meds:
                try:
                    text += format_medication_info(med) + "\n\n"
                except Exception as e:
                    self.app.logger.error(f"Ошибка форматирования лекарства {med[0]}: {e}")
                    text += f"⚠️ Лекарство ID {med[0]} - ошибка данных\n\n"
            
            await self._send_message(user_id, text, parse_mode="HTML")
        except Exception as e:
            self.app.logger.error(f"Ошибка отправки списка лекарств: {e}")
            await self._send_message(user_id, "❌ Произошла ошибка при загрузке данных. Попробуйте позже.")
    
    async def _send_message(self, user_id: int, text: str, parse_mode=None):
        """
        Общий метод отправки сообщений
        
        Args:
            user_id (int): ID пользователя
            text (str): Текст сообщения
            parse_mode (str, optional): Режим форматирования. По умолчанию None.
        """
        try:
            await self.app.bot.send_message(
                chat_id=user_id, 
                text=text, 
                parse_mode=parse_mode
            )
        except Exception as e:
            self.app.logger.error(f"Ошибка отправки сообщения: {e}")
