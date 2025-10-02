
import sqlite3
from sqlite3 import Error
from ..core.logger import logger

class Database:
    def __init__(self, db_file):
        self.logger = logger.getChild('Database')
        self.connection = sqlite3.connect(db_file)

    def create_tables(self):
        """
        Создание всех необходимых таблиц, включая историю приёмов
        """
        with self.connection:
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    zodiac_sign TEXT,
                    send_horoscope INTEGER,
                    send_weather INTEGER
                )
            ''')
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS medications (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    name TEXT,
                    dose_per_intake INTEGER,
                    intakes_per_day INTEGER,
                    start_date TEXT,
                    duration_value INTEGER,
                    duration_unit TEXT,
                    break_value INTEGER,
                    break_unit TEXT,
                    cycles INTEGER
                )
            ''')
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS medication_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    medication_id INTEGER,
                    user_id INTEGER,
                    event_type TEXT,
                    event_date TEXT,
                    cycles_before INTEGER,
                    cycles_after INTEGER,
                    start_date_before TEXT,
                    start_date_after TEXT,
                    comment TEXT
                )
            ''')
        self.migrate_medication_history()

    def migrate_medication_history(self):
        """
        Заполнить таблицу medication_history начальными данными из medications (однократно)
        """
        with self.connection:
            meds = self.connection.execute('SELECT * FROM medications').fetchall()
            for med in meds:
                exists = self.connection.execute(
                    'SELECT 1 FROM medication_history WHERE medication_id = ? AND event_type = ? LIMIT 1',
                    (med[0], 'start')
                ).fetchone()
                if not exists:
                    self.connection.execute(
                        '''INSERT INTO medication_history (
                            medication_id, user_id, event_type, event_date, cycles_before, cycles_after, start_date_before, start_date_after, comment
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (
                            med[0], # medication_id
                            med[1], # user_id
                            'start',
                            med[5], # start_date (используем как дату события)
                            med[10], # cycles_before
                            med[10], # cycles_after (на момент старта они равны)
                            med[5],  # start_date_before
                            med[5],  # start_date_after
                            'Initial import from medications'
                        )
                    )

    def create_user_settings_table(self):
        sql = """
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            zodiac_sign TEXT,
            send_horoscope INTEGER DEFAULT 1,
            send_weather INTEGER DEFAULT 0
        );
        """
        self.connection.execute(sql)
        self.connection.commit()

    def update_user_settings_table(self):
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'")
            if not cursor.fetchone():
                self.logger.info("Таблица user_settings не существует, обновление не требуется")
                return
            cursor.execute("PRAGMA table_info(user_settings)")
            columns = {column[1]: column for column in cursor.fetchall()}
            self.logger.info(f"Текущие колонки в таблице user_settings: {list(columns.keys())}")
            if 'name' not in columns:
                self.logger.info("Добавляем колонку 'name' в таблицу user_settings")
                self.connection.execute("ALTER TABLE user_settings ADD COLUMN name TEXT")
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении структуры user_settings: {e}", exc_info=True)

    def get_medications(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM medications WHERE user_id=?", (user_id,))
        return cursor.fetchall()

    def get_medication_by_id(self, med_id):
        cursor = self.connection.cursor()
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
            cursor = self.connection.cursor()
            cursor.execute(sql, values)
            self.connection.commit()

            # Проверяем количество обновленных строк
            if cursor.rowcount == 0:
                raise ValueError("Запись не найдена или данные не изменились")

        except sqlite3.Error as e:
            self.connection.rollback()
            raise Exception(f"Ошибка базы данных: {str(e)}")

    def delete_medication(self, med_id):
        self.connection.execute("DELETE FROM medications WHERE id=?", (med_id,))
        self.connection.commit()

    def get_all_medications(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM medications")
        return cursor.fetchall()

    def get_all_users(self):
        """Возвращает список ID пользователей (чисел), которые зарегистрированы в боте"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT DISTINCT user_id FROM user_settings")
        return [user_id for (user_id,) in cursor.fetchall()]  # Явное распаковывание кортежа

    def get_medication_field_names(self):
        """Возвращает список полей лекарства"""
        cursor = self.connection.cursor()
        cursor.execute("PRAGMA table_info(medications)")
        return [column[1] for column in cursor.fetchall()]

    def add_user_settings(self, user_id: int, name: str = None, zodiac_sign: str = None, 
                          send_horoscope: bool = True, send_weather: bool = False):
        """Сохраняет настройки пользователя"""
        try:
            self.logger.info(f"Сохранение настроек пользователя: user_id={user_id}, name={name}, "
                           f"zodiac_sign={zodiac_sign}, send_horoscope={send_horoscope}, send_weather={send_weather}")
            
            # Проверяем, существует ли таблица
            cursor = self.connection.cursor()
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
                
                self.connection.execute(sql, (user_id, name, zodiac_sign, send_horoscope_int, send_weather_int))
            else:
                # Если таблица старая, используем старый формат
                self.logger.warning("Используем старый формат таблицы user_settings")
                sql = """
                INSERT OR REPLACE INTO user_settings (user_id, zodiac_sign)
                VALUES (?, ?)
                """
                self.connection.execute(sql, (user_id, zodiac_sign))
            
            self.connection.commit()
            self.logger.info("Настройки пользователя успешно сохранены")
            
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении настроек пользователя: {e}", exc_info=True)
            self.connection.rollback()
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
