import re
from datetime import datetime

def validate_date(date_str: str) -> bool:
    """
    Проверка формата даты (ГГГГ-ММ-ДД)
    
    Args:
        date_str (str): Строка с датой для проверки
    
    Returns:
        bool: True если дата валидна, иначе False
    """
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_number(text: str, min_val: int = 1, max_val: int = None) -> bool:
    """
    Проверка что текст - число в диапазоне
    
    Args:
        text (str): Строка для проверки
        min_val (int, optional): Минимальное значение. По умолчанию 1.
        max_val (int, optional): Максимальное значение. По умолчанию None.
    
    Returns:
        bool: True если число валидно, иначе False
    """
    if not text.isdigit():
        return False
    num = int(text)
    if num < min_val:
        return False
    if max_val is not None and num > max_val:
        return False
    return True

def validate_unit(text: str) -> bool:
    """
    Проверка допустимых значений (days/months)
    
    Args:
        text (str): Строка для проверки
    
    Returns:
        bool: True если значение валидно, иначе False
    """
    return text.lower() in ['days', 'months']

def validate_zodiac_sign(sign: str) -> bool:
    """
    Проверка валидности знака зодиака
    
    Args:
        sign (str): Знак зодиака для проверки
    
    Returns:
        bool: True если знак валиден, иначе False
    """
    valid_signs = ['овен', 'телец', 'близнецы', 'рак', 'лев',
                  'дева', 'весы', 'скорпион', 'стрелец',
                  'козерог', 'водолей', 'рыбы']
    return sign.lower() in valid_signs
