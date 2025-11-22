from bot.database import get_db, User

def remove_test_users():
    """Удаляет тестовых пользователей Иванова, Петрова, Сидорову"""
    db = get_db()
    
    test_users = ["Иванов Иван Иванович", "Петров Петр Петрович", "Сидорова Анна Владимировна"]
    
    for user_name in test_users:
        user = db.query(User).filter(User.fio == user_name).first()
        if user:
            db.delete(user)
            print(f"✅ Удален пользователь: {user_name}")
        else:
            print(f"ℹ️ Пользователь не найден: {user_name}")
    
    db.commit()
    db.close()
    print("🎯 Удаление тестовых пользователей завершено!")



if __name__ == "__main__":
    print("🛠️ Управление пользователями")
    remove_test_users()