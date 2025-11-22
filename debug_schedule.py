from bot.handlers.schedule_handler import schedule_menu
from aiogram import types
from bot.database import create_user, UserRole, get_user_by_telegram_id
import asyncio

async def test_schedule_menu():
    print("🧪 Тестируем меню расписания...")
    
    # Создаем тестовое сообщение
    class MockMessage:
        def __init__(self, user_id, role):
            self.from_user = type('User', (), {'id': user_id})()
            self.text = "📅 Календарь смен"
            self.answer = self.mock_answer
            self.user_role = role
        
        async def mock_answer(self, text, reply_markup=None, parse_mode=None):
            print(f"📨 Бот отвечает: {text}")
            if reply_markup:
                print("⌨️ Клавиатура:")
                for row in reply_markup.keyboard:
                    row_text = [btn.text for btn in row]
                    print(f"   {row_text}")
            return True
    
    # Тестируем для сотрудника
    employee_msg = MockMessage(1000000002, "employee")
    print("\n👤 Тестируем для сотрудника:")
    await schedule_menu(employee_msg)
    
    # Тестируем для мастера
    master_msg = MockMessage(1000000001, "master") 
    print("\n👨‍🏭 Тестируем для мастера:")
    await schedule_menu(master_msg)

if __name__ == "__main__":
    asyncio.run(test_schedule_menu())