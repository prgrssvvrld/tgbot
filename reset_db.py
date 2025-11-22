import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3
from bot.database import Base, engine
from bot.database import create_user, UserRole

def reset_database():
    """Полностью пересоздает базу данных с тестовыми данными"""
    print("🔄 Сброс базы данных...")
    
    db_path = "rusal_bot.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️ Старая база данных удалена")
    
    Base.metadata.create_all(bind=engine)
    print("✅ Новая база данных создана")
    
    print("\n🎉 База данных пересоздана успешно!")

def check_database():
    """Проверяет состояние базы данных"""
    print("\n🔍 Проверка базы данных...")
    
    db_path = "rusal_bot.db"
    if not os.path.exists(db_path):
        print("❌ База данных не существует")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📊 Таблицы в базе: {[table[0] for table in tables]}")
        
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"👥 Пользователей в базе: {user_count}")
        
        cursor.execute("SELECT COUNT(*) FROM events") 
        event_count = cursor.fetchone()[0]
        print(f"📋 Событий в базе: {event_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки базы: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🛠️  УТИЛИТА ДЛЯ УПРАВЛЕНИЯ БАЗОЙ ДАННЫХ")
    print("=" * 50)
    
    if check_database():
        response = input("\n❓ База данных существует. Пересоздать? (y/n): ")
        if response.lower() == 'y':
            reset_database()
        else:
            print("❌ Операция отменена")
    else:
        reset_database()
    
    print("\n" + "=" * 50)