# create_test_events.py
from bot.database import create_event, get_user_by_telegram_id, EventType
import datetime

def create_test_events():
    print("🎯 СОЗДАНИЕ ТЕСТОВЫХ СОБЫТИЙ")
    
    # Находим пользователя
    user = get_user_by_telegram_id(1000000002)  # Петров
    if not user:
        print("❌ Пользователь не найден")
        return
    
    # Создаем событие прямо сейчас
    event = create_event(
        user_id=user.id,
        user_fio=user.fio,
        event_type=EventType.BREAKDOWN,
        description="ТЕСТОВОЕ СОБЫТИЕ ДЛЯ PDF ОТЧЕТА"
    )
    
    print(f"✅ Создано событие: {event.description}")
    print(f"   Время: {event.timestamp}")
    print(f"   ID: {event.id}")

if __name__ == "__main__":
    create_test_events()