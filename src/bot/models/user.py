class User:
    """
    Модель пользователя бота
    """
    def __init__(self, user_id: int, zodiac_sign: str = None):
        """
        Инициализация пользователя
        
        Args:
            user_id (int): ID пользователя в Telegram
            zodiac_sign (str, optional): Знак зодиака пользователя. По умолчанию None.
        """
        self.user_id = user_id
        self.zodiac_sign = zodiac_sign
    
    def to_dict(self):
        """
        Преобразование в словарь для сохранения
        
        Returns:
            dict: Словарь с данными пользователя
        """
        return {
            'user_id': self.user_id,
            'zodiac_sign': self.zodiac_sign
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
            zodiac_sign=data.get('zodiac_sign')
        )
