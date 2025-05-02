from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from database import Database

def setup_scheduler(app, db):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_medications,
        "interval",
        minutes=30,
        args=[app, db],
    )
    scheduler.start()

async def send_daily_notification(app, db):
    now = datetime.now()
    if now.hour != 9:  # Проверяем только в 9 утра
        return

    all_meds = db.get_all_medications()  # Новый метод в database.py
    for user_id in set(med[1] for med in all_meds):
        user_meds = [m for m in all_meds if m[1] == user_id]
        message = "💊 Лекарства на сегодня:\n\n"

        for med in user_meds:
            start_date = datetime.strptime(med[5], "%Y-%m-%d")
            duration = timedelta(days=med[6]) if med[7] == "days" else timedelta(days=med[6]*30)
            end_date = start_date + duration
            days_left = (end_date - now).days

            if days_left > 0:
                message += (
                    f"• {med[2]} — {med[3]} капс. × {med[4]} р/день\n"
                    f"  📅 Осталось: {days_left} дней\n\n"
                )
            else:
                next_cycle = end_date + timedelta(days=med[8]) if med[9] == "days" else end_date + timedelta(days=med[8]*30)
                message += (
                    f"• {med[2]} — перерыв до {next_cycle.strftime('%d/%m/%Y')}\n\n"
                )

        await app.bot.send_message(user_id, message)

async def check_medications(app, db):
    # Здесь будет логика проверки времени приема
    pass