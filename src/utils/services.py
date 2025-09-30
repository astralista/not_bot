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
                params={'fsyms': 'BTC,ETH,TON,SOL,NC,GRASS', 'tsyms': 'USD'}
            ).json()

            # Функция для форматирования чисел с разделителем тысяч
            def format_price(price):
                # Форматируем с разделителями тысяч и 2 знаками после запятой
                return f"{price:,.2f}".replace(",", "'")

            # Собираем все данные
            lines = []
            lines.append(("USD/RUB", format_price(usd_rub)))  # Применяем форматирование

            for coin in ['BTC', 'ETH', 'TON', 'SOL', 'NC', 'GRASS']:
                price = crypto_data[coin]['USD']
                formatted_price = f"${format_price(price)}"  # Применяем форматирование
                lines.append((coin, formatted_price))

            # Находим максимальные длины
            max_name_len = max(len(name) for name, _ in lines)
            max_price_len = max(len(price) for _, price in lines)

            # Формируем результат с моноширинным шрифтом через <code>
            result = ["<b>💱 Курсы:</b>"]
            for name, price in lines:
                # Создаем строку с точками и выравниванием
                dots_needed = max_name_len - len(name) + 3  # +3 для отступа
                dots = '.' * dots_needed
                result.append(f"<code>{name}: {dots}{price}</code>")

            return "\n".join(result)

        except Exception as e:
            logging.error(f"Exchange API error: {e}")
            return "Не удалось получить курсы валют"

    @staticmethod
    def get_horoscope(sign: str) -> str:
        """
        Парсинг гороскопа с новым селектором
        
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
            sign_en = signs.get(sign.lower(), 'aries')
            url = f"https://horo.mail.ru/prediction/{sign_en}/today/"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            page = requests.get(url, headers=headers, timeout=10)
            page.raise_for_status()
            
            soup = BeautifulSoup(page.content, 'html.parser')
            
            # Новый селектор на основе предоставленной структуры
            main_content = soup.find('main', {'itemprop': 'articleBody'})
            
            if main_content:
                # Собираем все параграфы внутри div с классом 'b6a5d4949c'
                paragraphs = []
                for div in main_content.find_all('div', class_='b6a5d4949c'):
                    paragraphs.extend(p.text.strip() for p in div.find_all('p'))
                
                if paragraphs:
                    text = '\n\n'.join(paragraphs)
                    return f"♋ Гороскоп для {sign} на сегодня:\n\n{text}"
            
            return f"Не удалось найти текст гороскопа для {sign}"
                
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
