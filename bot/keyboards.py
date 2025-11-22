from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

def get_main_keyboard(role: str):
    keyboard = []
    
    if role == "master":
        keyboard = [
            [KeyboardButton(text="📊 Создать событие")],
            [KeyboardButton(text="📋 Журнал событий"), KeyboardButton(text="👥 Поиск сотрудника")],
            [KeyboardButton(text="📄 Отчет за день"), KeyboardButton(text="📅 Календарь смен")]
        ]
    else:
        keyboard = [
            [KeyboardButton(text="📊 Создать событие")],
            [KeyboardButton(text="ℹ️ Мой статус"), KeyboardButton(text="📅 Календарь смен")]  
        ]
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_event_type_keyboard():
    keyboard = [
        [KeyboardButton(text="🛑 Остановка оборудования")],
        [KeyboardButton(text="🔧 Поломка"), KeyboardButton(text="📝 Другое")],
        [KeyboardButton(text="❌ Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_cancel_keyboard():
    keyboard = [
        [KeyboardButton(text="❌ Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_remove_keyboard():
    return ReplyKeyboardRemove()
def get_role_keyboard():
    keyboard = [
        [KeyboardButton(text="👨‍💼 Сотрудник")],
        [KeyboardButton(text="👨‍🏭 Мастер смены")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
def get_schedule_keyboard():
    """Клавиатура для сотрудников"""
    keyboard = [
        [KeyboardButton(text="📅 Мое расписание")],
        [KeyboardButton(text="✏️ Запланировать отпуск/больничный")],
        [KeyboardButton(text="⬅️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
def get_employee_management_keyboard():
    """Клавиатура для мастера"""
    keyboard = [
        [KeyboardButton(text="👀 Просмотр расписания")],
        [KeyboardButton(text="✏️ Редактировать расписание")],
        [KeyboardButton(text="📊 Общий календарь")],
        [KeyboardButton(text="⬅️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
def get_status_keyboard():
    keyboard = [
        [KeyboardButton(text="🟢 Работаю")],
        [KeyboardButton(text="🟡 Отпуск")],
        [KeyboardButton(text="🔴 Больничный")],
        [KeyboardButton(text="❌ Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
def get_date_keyboard():
    """Клавиатура с датами на 2 недели вперед"""
    import datetime
    keyboard = []
    row = []
    
    today = datetime.datetime.now().date()
    for i in range(14):
        current_date = today + datetime.timedelta(days=i)
        row.append(KeyboardButton(text=current_date.strftime("%d.%m")))
        
        if len(row) == 3:  
            keyboard.append(row)
            row = []
    
    if row:  
        keyboard.append(row)
    
    keyboard.append([KeyboardButton(text="❌ Отмена")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
def get_back_to_schedule_keyboard():
    """Клавиатура для возврата в меню расписания"""
    keyboard = [
        [KeyboardButton(text="⬅️ Назад в расписание")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)