from dotenv import load_dotenv
load_dotenv()
import os

from bot import MedicationBot

if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("Токен бота не найден!")

    bot = MedicationBot(TOKEN)
    bot.run()