import os

import requests
import random
from datetime import datetime
import logging

from bs4 import BeautifulSoup


class Services:
    @staticmethod
    def get_weather(city: str) -> str:
        """
        Получаем погоду через OpenWeatherMap API
        
        Args:
            city (str): Название города
        
        Returns:
            str: Строка с информацией о погоде
        """
        api_key = os.getenv("OpenWeatherAPI")  # Получите на openweathermap.org
        base_url = "http://api.openweathermap.org/data/2.5/weather"

        params = {
            'q': city,
            'appid': api_key,
            'units': 'metric',
            'lang': 'ru'
        }

        try:
            response = requests.get(base_url, params=params)
            data = response.json()
            return (f"🌤 Погода в {city}:\n"
                    f"Температура: {data['main']['temp']}°C\n"
                    f"Ощущается как: {data['main']['feels_like']}°C\n"
                    f"Влажность: {data['main']['humidity']}%\n"
                    f"Ветер: {data['wind']['speed']} м/с")
        except Exception as e:
            logging.error(f"Weather API error: {e}")
            return f"Не удалось получить погоду для {city}"

    @staticmethod
    def get_exchange_rates() -> str:
        """
        Курсы валют через CryptoCompare API
        
        Returns:
            str: Строка с информацией о курсах валют
        """
        try:
            # Курсы фиата
            usd_rub = requests.get("https://api.exchangerate-api.com/v4/latest/USD").json()['rates']['RUB']

            # Криптовалюты
            crypto_data = requests.get(
                "https://min-api.cryptocompare.com/data/pricemulti",
                params={'fsyms': 'BTC,ETH,TON', 'tsyms': 'USD'}
            ).json()

            return (f"💱 Курсы:\n"
                    f"USD/RUB: {usd_rub:.2f}\n"
                    f"BTC: ${crypto_data['BTC']['USD']}\n"
                    f"ETH: ${crypto_data['ETH']['USD']}\n"
                    f"TON: ${crypto_data['TON']['USD']}")
        except Exception as e:
            logging.error(f"Exchange API error: {e}")
            return "Не удалось получить курсы валют"

    @staticmethod
    def get_horoscope(sign: str) -> str:
        """
        Парсинг гороскопа
        
        Args:
            sign (str): Знак зодиака
        
        Returns:
            str: Строка с гороскопом
        """
        signs = {
            'овен': 'aries',
            'телец': 'taurus',
            'близнецы': 'gemini',
            'рак': 'cancer',
            'лев': 'leo',
            'дева': 'virgo',
            'весы': 'libra',
            'скорпион': 'scorpio',
            'стрелец': 'sagittarius',
            'козерог': 'capricorn',
            'водолей': 'aquarius',
            'рыбы': 'pisces'
        }

        try:
            sign_en = signs.get(sign.lower(), 'aries')  # По умолчанию овен
            url = f"https://horo.mail.ru/prediction/{sign_en}/today/"
            page = requests.get(url)
            soup = BeautifulSoup(page.content, 'html.parser')
            text = soup.find('div', class_='article__text').text.strip()
            return f"♌ Гороскоп для {sign}:\n{text[:500]}..."  # Ограничиваем длину
        except Exception as e:
            logging.error(f"Horoscope error: {e}")
            return f"Не удалось получить гороскоп для {sign}"

    @staticmethod
    def get_daily_quote() -> str:
        """
        Случайная мотивационная цитата
        
        Returns:
            str: Строка с цитатой
        """
        quotes = [
            "Сегодня лучший день, чтобы начать!",
            "Маленькие шаги приводят к большим результатам.",
            "Успех — это сумма небольших усилий, повторяющихся изо дня в день.",
            "Никогда не поздно стать тем, кем вы всегда хотели быть.",
            "Ваше здоровье — ваше богатство.",
            "Забота о себе — это не эгоизм, а необходимость.",
            "Регулярность приема лекарств — ключ к эффективному лечению.",
            "Здоровье — это не просто отсутствие болезни, а состояние полного благополучия.",
            "Лучшее лекарство — это профилактика.",
            "Ваше тело — храм вашей души, заботьтесь о нем."
        ]
        return f"🌟 Цитата дня:\n{random.choice(quotes)}"
