from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from ...core.database import Database
from ...utils.helpers import calculate_next_notification

class SchedulerService:
    """
    Сервис для работы с планировщиком задач
    """
    def __init__(self, db: Database, bot_application):
        """
        Инициализация сервиса планировщика
        
        Args:
            db (Database): Экземпляр базы данных
            bot_application: Экземпляр приложения бота
        """
        self.db = db
        self.app = bot_application
        self.scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    
    def start(self):
        """
        Запуск планировщика
        """
        self.scheduler.start()
    
    def setup_medication_checks(self):
        """
        Настройка проверки лекарств каждые 30 минут
        """
        self.scheduler.add_job(
            self.check_medications,
            "interval",
            minutes=30,
            id="medication_check"
        )
    
    async def check_medications(self):
        """
        Проверка лекарств и отправка уведомлений
        """
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        
        # Получаем все лекарства из БД
        all_meds = self.db.get_all_medications()
        
        for med in all_meds:
            try:
                med_id, user_id, name, dose, intakes, start_date, duration_val, duration_unit, break_val, break_unit, cycles = med
                
                # Проверяем, активен ли прием лекарства сейчас
                if not start_date:
                    continue
                
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
                current_date = now.date()
                
                # Рассчитываем дату окончания приема
                duration_days = duration_val if duration_unit == "days" else duration_val * 30
                end_date = start_date_obj + timedelta(days=duration_days)
                
                # Если курс еще не начался или уже закончился, пропускаем
                if current_date < start_date_obj or current_date > end_date:
                    continue
                
                # Рассчитываем времена приема в течение дня
                notification_times = calculate_next_notification(start_date_obj, intakes)
                
                # Проверяем, совпадает ли текущее время с временем приема
                for notification_time in notification_times:
                    if notification_time.hour == current_hour and abs(notification_time.minute - current_minute) <= 15:
                        # Отправляем уведомление
                        await self.send_medication_reminder(user_id, name, dose)
                        break
            
            except Exception as e:
                self.app.logger.error(f"Ошибка при проверке лекарства {med[0]}: {e}")
    
    async def send_medication_reminder(self, user_id: int, med_name: str, dose: int):
        """
        Отправка напоминания о приеме лекарства
        
        Args:
            user_id (int): ID пользователя
            med_name (str): Название лекарства
            dose (int): Доза приема
        """
        try:
            message = f"💊 Напоминание: примите {dose} капсул(ы) {med_name}"
            await self.app.bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            self.app.logger.error(f"Ошибка отправки напоминания: {e}")
