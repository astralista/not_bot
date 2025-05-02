from database import Database

if __name__ == "__main__":
    print("Инициализация БД...")
    db = Database("/app/data/users.db")
    print("Таблицы созданы!")