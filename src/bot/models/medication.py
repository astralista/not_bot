from datetime import datetime, timedelta

class Medication:
    """
    Модель лекарства
    """
    def __init__(
        self,
        id: int = None,
        user_id: int = None,
        name: str = None,
        dose_per_intake: int = None,
        intakes_per_day: int = None,
        start_date: str = None,
        duration_value: int = None,
        duration_unit: str = None,
        break_value: int = None,
        break_unit: str = None,
        cycles: int = 1
    ):
        """
        Инициализация лекарства
        
        Args:
            id (int, optional): ID лекарства в БД. По умолчанию None.
            user_id (int, optional): ID пользователя. По умолчанию None.
            name (str, optional): Название лекарства. По умолчанию None.
            dose_per_intake (int, optional): Доза за один прием. По умолчанию None.
            intakes_per_day (int, optional): Количество приемов в день. По умолчанию None.
            start_date (str, optional): Дата начала приема (ГГГГ-ММ-ДД). По умолчанию None.
            duration_value (int, optional): Значение длительности приема. По умолчанию None.
            duration_unit (str, optional): Единица измерения длительности (days/months). По умолчанию None.
            break_value (int, optional): Значение длительности перерыва. По умолчанию None.
            break_unit (str, optional): Единица измерения перерыва (days/months). По умолчанию None.
            cycles (int, optional): Количество курсов. По умолчанию 1.
        """
        self.id = id
        self.user_id = user_id
        self.name = name
        self.dose_per_intake = dose_per_intake
        self.intakes_per_day = intakes_per_day
        self.start_date = start_date
        self.duration_value = duration_value
        self.duration_unit = duration_unit
        self.break_value = break_value
        self.break_unit = break_unit
        self.cycles = cycles
    
    def to_dict(self):
        """
        Преобразование в словарь для сохранения
        
        Returns:
            dict: Словарь с данными лекарства
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'dose_per_intake': self.dose_per_intake,
            'intakes_per_day': self.intakes_per_day,
            'start_date': self.start_date,
            'duration_value': self.duration_value,
            'duration_unit': self.duration_unit,
            'break_value': self.break_value,
            'break_unit': self.break_unit,
            'cycles': self.cycles
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """
        Создание объекта из словаря
        
        Args:
            data (dict): Словарь с данными лекарства
        
        Returns:
            Medication: Объект лекарства
        """
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id'),
            name=data.get('name'),
            dose_per_intake=data.get('dose_per_intake'),
            intakes_per_day=data.get('intakes_per_day'),
            start_date=data.get('start_date'),
            duration_value=data.get('duration_value'),
            duration_unit=data.get('duration_unit'),
            break_value=data.get('break_value'),
            break_unit=data.get('break_unit'),
            cycles=data.get('cycles', 1)
        )
    
    @classmethod
    def from_tuple(cls, data: tuple):
        """
        Создание объекта из кортежа (результат запроса к БД)
        
        Args:
            data (tuple): Кортеж с данными лекарства
        
        Returns:
            Medication: Объект лекарства
        """
        return cls(
            id=data[0],
            user_id=data[1],
            name=data[2],
            dose_per_intake=data[3],
            intakes_per_day=data[4],
            start_date=data[5],
            duration_value=data[6],
            duration_unit=data[7],
            break_value=data[8],
            break_unit=data[9],
            cycles=data[10] if len(data) > 10 else 1
        )
    
    def get_days_left(self):
        """
        Расчет оставшихся дней приема
        
        Returns:
            int: Количество оставшихся дней
        """
        if not self.start_date:
            return 0
        
        current_date = datetime.now().date()
        start_date = datetime.strptime(self.start_date, "%Y-%m-%d").date()
        
        duration_days = self.duration_value if self.duration_unit == "days" else self.duration_value * 30
        end_date = start_date + timedelta(days=duration_days)
        
        return (end_date - current_date).days
    
    def get_next_cycle_date(self):
        """
        Расчет даты начала следующего курса
        
        Returns:
            datetime.date: Дата начала следующего курса
        """
        if not self.start_date:
            return None
        
        start_date = datetime.strptime(self.start_date, "%Y-%m-%d").date()
        
        duration_days = self.duration_value if self.duration_unit == "days" else self.duration_value * 30
        end_date = start_date + timedelta(days=duration_days)
        
        break_days = self.break_value if self.break_unit == "days" else self.break_value * 30
        next_cycle = end_date + timedelta(days=break_days)
        
        return next_cycle
