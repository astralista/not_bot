import sqlite3
from sqlite3 import Error
from ..core.logger import logger

class Database:
    def __init__(self, db_file):
        self.logger = logger.getChild('Database')
        self.conn = self.create_connection(db_file)
        self.create_table()
        self.create_user_settings_table()  # Создаем таблицу настроек при инициализации
        self.update_user_settings_table()  # Обновляем структуру таблицы, если нужно

    def create_connection(self, db_file):
        conn = None
        try:
            conn = sqlite3.connect(db_file)
            return conn
        except Error as e:
            print(e)
        return conn

    def create_table(self):
        sql = """
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            dose_per_intake INTEGER NOT NULL,
            intakes_per_day INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            duration_value INTEGER NOT NULL,
            duration_unit TEXT NOT NULL,
            break_value INTEGER NOT NULL,
            break_unit TEXT NOT NULL,
            cycles INTEGER DEFAULT 1
        );
        """
        self.conn.execute(sql)
        self.conn.commit()

    def create_user_settings_table(self):
        """Создает таблицу для настроек пользователя, если её нет"""
        sql = """
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            zodiac_sign TEXT,
            send_horoscope INTEGER DEFAULT 1,
            send_weather INTEGER DEFAULT 0
        );
        """
        self.conn.execute(sql)
        self.conn.commit()
        
    def update_user_settings_table(self):
        """Обновляет структуру таблицы user_settings, если она уже существует"""
        try:
            # Проверяем, существует ли таблица
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'")
            if not cursor.fetchone():
                self.logger.info("Таблица user_settings не существует, обновление не требуется")
                return
                
            # Проверяем структуру таблицы
            cursor.execute("PRAGMA table_info(user_settings)")
            columns = {column[1]: column for column in cursor.fetchall()}
            self.logger.info(f"Текущие колонки в таблице user_settings: {list(columns.keys())}")
            
            # Добавляем недостающие колонки
            if 'name' not in columns:
                self.logger.info("Добавляем колонку 'name' в таблицу user_settings")
                self.conn.execute("ALTER TABLE user_settings ADD COLUMN name TEXT")
                
            if 'send_horoscope' not in columns:
                self.logger.info("Добавляем колонку 'send_horoscope' в таблицу user_settings")
                self.conn.execute("ALTER TABLE user_settings ADD COLUMN send_horoscope INTEGER DEFAULT 1")
                
            if 'send_weather' not in columns:
                self.logger.info("Добавляем колонку 'send_weather' в таблицу user_settings")
                self.conn.execute("ALTER TABLE user_settings ADD COLUMN send_weather INTEGER DEFAULT 0")
                
            self.conn.commit()
            self.logger.info("Структура таблицы user_settings успешно обновлена")
            
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении структуры таблицы user_settings: {e}", exc_info=True)
            self.conn.rollback()

    def add_medication(self, user_id, name, dose_per_intake, intakes_per_day, start_date,
                      duration_value, duration_unit, break_value, break_unit, cycles=1):
        sql = """
        INSERT INTO medications(
            user_id, name, dose_per_intake, intakes_per_day, start_date,
            duration_value, duration_unit, break_value, break_unit, cycles
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(sql, (
            user_id, name, dose_per_intake, intakes_per_day, start_date,
            duration_value, duration_unit, break_value, break_unit, cycles
        ))
        self.conn.commit()

    def get_medications(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM medications WHERE user_id=?", (user_id,))
        return cursor.fetchall()

    def get_medication_by_id(self, med_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM medications WHERE id=?", (med_id,))
        return cursor.fetchone()

    def update_medication(self, med_id: int, **kwargs):
        """Обновляет данные лекарства с проверкой полей"""
        if not kwargs:
            raise ValueError("Нет данных для обновления")

        # Получаем допустимые поля
        allowed_fields = self.get_medication_field_names()
        for field in kwargs.keys():
            if field not in allowed_fields:
                raise ValueError(f"Недопустимое поле: {field}")

        # Формируем SQL-запрос
        set_clause = ", ".join([f"{field} = ?" for field in kwargs.keys()])
        values = list(kwargs.values())
        values.append(med_id)

        sql = f"UPDATE medications SET {set_clause} WHERE id = ?"

        # Выполняем с транзакцией
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, values)
            self.conn.commit()

            # Проверяем количество обновленных строк
            if cursor.rowcount == 0:
                raise ValueError("Запись не найдена или данные не изменились")

        except sqlite3.Error as e:
            self.conn.rollback()
            raise Exception(f"Ошибка базы данных: {str(e)}")

    def delete_medication(self, med_id):
        self.conn.execute("DELETE FROM medications WHERE id=?", (med_id,))
        self.conn.commit()

    def get_all_medications(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM medications")
        return cursor.fetchall()

    def get_all_users(self):
        """Возвращает список ID пользователей (чисел), которые зарегистрированы в боте"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT user_id FROM user_settings")
        return [user_id for (user_id,) in cursor.fetchall()]  # Явное распаковывание кортежа

    def get_medication_field_names(self):
        """Возвращает список полей лекарства"""
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(medications)")
        return [column[1] for column in cursor.fetchall()]

    def add_user_settings(self, user_id: int, name: str = None, zodiac_sign: str = None, 
                          send_horoscope: bool = True, send_weather: bool = False):
        """Сохраняет настройки пользователя"""
        try:
            self.logger.info(f"Сохранение настроек пользователя: user_id={user_id}, name={name}, "
                           f"zodiac_sign={zodiac_sign}, send_horoscope={send_horoscope}, send_weather={send_weather}")
            
            # Проверяем, существует ли таблица
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'")
            if not cursor.fetchone():
                self.logger.warning("Таблица user_settings не существует, создаем...")
                self.create_user_settings_table()
            
            # Проверяем структуру таблицы
            cursor.execute("PRAGMA table_info(user_settings)")
            columns = [column[1] for column in cursor.fetchall()]
            self.logger.info(f"Колонки в таблице user_settings: {columns}")
            
            # Формируем SQL-запрос в зависимости от структуры таблицы
            if all(col in columns for col in ['name', 'send_horoscope', 'send_weather']):
                sql = """
                INSERT OR REPLACE INTO user_settings (user_id, name, zodiac_sign, send_horoscope, send_weather)
                VALUES (?, ?, ?, ?, ?)
                """
                # Преобразуем булевы значения в целые числа для SQLite
                send_horoscope_int = 1 if send_horoscope else 0
                send_weather_int = 1 if send_weather else 0
                
                self.conn.execute(sql, (user_id, name, zodiac_sign, send_horoscope_int, send_weather_int))
            else:
                # Если таблица старая, используем старый формат
                self.logger.warning("Используем старый формат таблицы user_settings")
                sql = """
                INSERT OR REPLACE INTO user_settings (user_id, zodiac_sign)
                VALUES (?, ?)
                """
                self.conn.execute(sql, (user_id, zodiac_sign))
            
            self.conn.commit()
            self.logger.info("Настройки пользователя успешно сохранены")
            
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении настроек пользователя: {e}", exc_info=True)
            self.conn.rollback()
            raise

    def get_user_zodiac(self, user_id: int) -> str:
        """Возвращает знак зодиака пользователя"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT zodiac_sign FROM user_settings WHERE user_id = ?",
            (user_id,)
        )
        result = cursor.fetchone()
        return result[0] if result else None
        
    def get_user_settings(self, user_id: int) -> dict:
        """Возвращает все настройки пользователя"""
        try:
            # Проверяем, существует ли таблица
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'")
            if not cursor.fetchone():
                self.logger.warning("Таблица user_settings не существует при попытке получить настройки")
                return None
                
            cursor.execute(
                "SELECT * FROM user_settings WHERE user_id = ?",
                (user_id,)
            )
            result = cursor.fetchone()
            
            if not result:
                return None
                
            # Получаем имена колонок
            column_names = [description[0] for description in cursor.description]
            
            # Создаем словарь с данными пользователя
            user_data = dict(zip(column_names, result))
            
            # Преобразуем целые числа в булевы значения
            if 'send_horoscope' in user_data:
                user_data['send_horoscope'] = bool(user_data['send_horoscope'])
            if 'send_weather' in user_data:
                user_data['send_weather'] = bool(user_data['send_weather'])
                
            # Добавляем значения по умолчанию для отсутствующих полей
            if 'name' not in user_data:
                user_data['name'] = None
            if 'send_horoscope' not in user_data:
                user_data['send_horoscope'] = True
            if 'send_weather' not in user_data:
                user_data['send_weather'] = False
                
            return user_data
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении настроек пользователя: {e}", exc_info=True)
            return None
