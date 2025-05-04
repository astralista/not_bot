import sqlite3
from sqlite3 import Error
from ..core.logger import logger

class Database:
    def __init__(self, db_file):
        self.logger = logger.getChild('Database')
        self.conn = self.create_connection(db_file)
        self.create_table()
        self.create_user_settings_table()  # Создаем таблицу настроек при инициализации

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
            zodiac_sign TEXT
        );
        """
        self.conn.execute(sql)
        self.conn.commit()

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
        """Возвращает список ID пользователей (чисел), которые добавили лекарства"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT user_id FROM medications")
        return [user_id for (user_id,) in cursor.fetchall()]  # Явное распаковывание кортежа

    def get_medication_field_names(self):
        """Возвращает список полей лекарства"""
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(medications)")
        return [column[1] for column in cursor.fetchall()]

    def add_user_settings(self, user_id: int, zodiac_sign: str):
        """Сохраняет настройки пользователя"""
        sql = """
        INSERT OR REPLACE INTO user_settings (user_id, zodiac_sign)
        VALUES (?, ?)
        """
        self.conn.execute(sql, (user_id, zodiac_sign))
        self.conn.commit()

    def get_user_zodiac(self, user_id: int) -> str:
        """Возвращает знак зодиака пользователя"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT zodiac_sign FROM user_settings WHERE user_id = ?",
            (user_id,)
        )
        result = cursor.fetchone()
        return result[0] if result else None
