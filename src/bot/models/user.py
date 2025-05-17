class User:
    """
    Модель пользователя бота
    """
    def __init__(self, user_id: int, name: str = None, zodiac_sign: str = None, 
                 send_horoscope: bool = True, send_weather: bool = False):
        """
        Инициализация пользователя
        
        Args:
            user_id (int): ID пользователя в Telegram
            name (str, optional): Имя пользователя. По умолчанию None.
            zodiac_sign (str, optional): Знак зодиака пользователя. По умолчанию None.
            send_horoscope (bool, optional): Отправлять ли гороскоп. По умолчанию True.
            send_weather (bool, optional): Отправлять ли прогноз погоды. По умолчанию False.
        """
        self.user_id = user_id
        self.name = name
        self.zodiac_sign = zodiac_sign
        self.send_horoscope = send_horoscope
        self.send_weather = send_weather
    
    def to_dict(self):
        """
        Преобразование в словарь для сохранения
        
        Returns:
            dict: Словарь с данными пользователя
        """
        return {
            'user_id': self.user_id,
            'name': self.name,
            'zodiac_sign': self.zodiac_sign,
            'send_horoscope': self.send_horoscope,
            'send_weather': self.send_weather
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """
        Создание объекта из словаря
        
        Args:
            data (dict): Словарь с данными пользователя
        
        Returns:
            User: Объект пользователя
        """
        return cls(
            user_id=data.get('user_id'),
            name=data.get('name'),
            zodiac_sign=data.get('zodiac_sign'),
            send_horoscope=data.get('send_horoscope', True),
            send_weather=data.get('send_weather', False)
        )
