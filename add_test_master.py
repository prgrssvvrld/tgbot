from bot.database import create_user, UserRole

def add_test_master():
    """Добавляет тестового мастера для демонстрации"""
    # Замените TELEGRAM_ID на реальный ID вашего аккаунта мастера
    master = create_user(
        telegram_id=1039471466,  # ЗАМЕНИТЕ НА РЕАЛЬНЫЙ ID
        fio="Храменков Александр Константинович",
        role=UserRole.MASTER,
        shift="Смена 1"
    )
    print(f"✅ Создан мастер: {master.fio}")

if __name__ == "__main__":
    add_test_master()