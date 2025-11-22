from bot.database import get_db, Event
import datetime

def fix_event_times():
    """Исправляет время событий в базе данных (добавляет 3 часа)"""
    print("🕒 Исправление времени событий...")
    
    db = get_db()
    
    try:
        # Получаем все события
        events = db.query(Event).all()
        print(f"📊 Найдено событий: {len(events)}")
        
        for event in events:
            # Добавляем 3 часа к каждому событию
            new_time = event.timestamp + datetime.timedelta(hours=3)
            event.timestamp = new_time
            print(f"   🔧 Исправлено: {event.id} -> {new_time}")
        
        db.commit()
        print("✅ Время событий исправлено")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_event_times()