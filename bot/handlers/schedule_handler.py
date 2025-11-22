from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram import Dispatcher
from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.database import (
    get_user_by_telegram_id, get_all_employees, 
    set_user_schedule, get_user_schedule, UserStatus,
    search_employees_by_name, UserRole, get_user_by_id
)
from bot.keyboards import (
    get_main_keyboard, get_schedule_keyboard, 
    get_status_keyboard, get_cancel_keyboard,
    get_date_keyboard, get_employee_management_keyboard
)
from bot.states import ScheduleStates

async def cancel_schedule_handler(message: types.Message, state: FSMContext):
    """Обработчик отмены для всех состояний расписания"""
    if message.text == "❌ Отмена":
        await state.clear()
        user = get_user_by_telegram_id(message.from_user.id)
        await message.answer(
            "Операция отменена", 
            reply_markup=get_main_keyboard(user.role.value)
        )
        return True
    return False

async def schedule_main_menu(message: types.Message, state: FSMContext):
    """Главное меню календаря смен"""
    await state.clear()
    user = get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer("❌ Вы не зарегистрированы. Введите /start для регистрации.")
        return
    
    if user.role == UserRole.MASTER:
        await message.answer(
            "📅 <b>Управление расписанием</b>\n\n"
            "Выберите действие:",
            reply_markup=get_employee_management_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "📅 <b>Мое расписание</b>\n\n"
            "Выберите действие:",
            reply_markup=get_schedule_keyboard(),
            parse_mode="HTML"
        )

def get_status_text_russian(status: UserStatus):
    """Возвращает русское название статуса"""
    status_text_map = {
        UserStatus.WORKING: "Работает",
        UserStatus.VACATION: "Отпуск", 
        UserStatus.SICK_LEAVE: "Больничный"
    }
    return status_text_map.get(status, status.value)

async def my_schedule(message: types.Message):
    """Показывает расписание текущего пользователя на 2 недели"""
    user = get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer("❌ Вы не зарегистрированы. Введите /start для регистрации.")
        return
    
    today = datetime.now().date()
    end_date = today + timedelta(days=14)
    
    schedule = get_user_schedule(user.id, today, end_date)
    
    response = f"📅 <b>Ваше расписание на 2 недели:</b>\n\n"
    
    current_date = today
    while current_date <= end_date:
        day_schedule = next((s for s in schedule if s.date == current_date), None)
        
        status_emoji = {
            UserStatus.WORKING: "🟢",
            UserStatus.VACATION: "🟡",
            UserStatus.SICK_LEAVE: "🔴"
        }
        
        status = day_schedule.status if day_schedule else UserStatus.WORKING
        emoji = status_emoji.get(status, "⚪")
        status_text = get_status_text_russian(status)
        
        response += f"{emoji} <b>{current_date.strftime('%d.%m')}</b> - {status_text}\n"
        
        current_date += timedelta(days=1)
    
    await message.answer(response, parse_mode="HTML")

async def plan_schedule_start(message: types.Message, state: FSMContext):
    """Начало планирования отпуска/больничного"""
    user = get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer("❌ Вы не зарегистрированы. Введите /start для регистрации.")
        return
    
    await message.answer(
        "Выберите дату для планирования:",
        reply_markup=get_date_keyboard()
    )
    await state.set_state(ScheduleStates.waiting_date)

async def process_schedule_date(message: types.Message, state: FSMContext):
    """Обработка выбранной даты"""
    if message.text == "❌ Отмена":
        await state.clear()
        user = get_user_by_telegram_id(message.from_user.id)
        await message.answer("Отменено", reply_markup=get_main_keyboard(user.role.value))
        return
    
    try:
        day, month = message.text.split('.')
        year = datetime.now().year
        selected_date = datetime(year, int(month), int(day)).date()
        
        today = datetime.now().date()
        max_date = today + timedelta(days=14)
        
        if selected_date < today:
            await message.answer("❌ Нельзя планировать на прошедшие даты")
            return
        if selected_date > max_date:
            await message.answer("❌ Можно планировать только на ближайшие 2 недели")
            return
        
        await state.update_data(selected_date=selected_date)
        await message.answer(
            "Выберите статус:",
            reply_markup=get_status_keyboard()
        )
        await state.set_state(ScheduleStates.waiting_status)
        
    except Exception as e:
        await message.answer("❌ Неверный формат даты. Используйте формат: 01.12")

async def process_schedule_status(message: types.Message, state: FSMContext):
    """Обработка выбранного статуса"""
    if message.text == "❌ Отмена":
        await state.clear()
        user = get_user_by_telegram_id(message.from_user.id)
        await message.answer("Отменено", reply_markup=get_main_keyboard(user.role.value))
        return
    
    status_mapping = {
        "🟢 Работаю": UserStatus.WORKING,
        "🟡 Отпуск": UserStatus.VACATION,
        "🔴 Больничный": UserStatus.SICK_LEAVE
    }
    
    if message.text not in status_mapping:
        await message.answer("❌ Пожалуйста, выберите статус используя кнопки")
        return
    
    data = await state.get_data()
    selected_date = data['selected_date']
    user = get_user_by_telegram_id(message.from_user.id)
    status = status_mapping[message.text]
    
    set_user_schedule(user.id, selected_date, status)
    
    await state.clear()
    
    status_emoji = {
        UserStatus.WORKING: "🟢",
        UserStatus.VACATION: "🟡", 
        UserStatus.SICK_LEAVE: "🔴"
    }
    
    await message.answer(
        f"✅ <b>Статус обновлен!</b>\n\n"
        f"📅 Дата: <b>{selected_date.strftime('%d.%m.%Y')}</b>\n"
        f"📊 Статус: {status_emoji[status]} {status.value}",
        reply_markup=get_main_keyboard(user.role.value),
        parse_mode="HTML"
    )

async def view_employee_schedule_start(message: types.Message, state: FSMContext):
    """Начало просмотра расписания сотрудников"""
    user = get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer("❌ Вы не зарегистрированы. Введите /start для регистрации.")
        return
    
    await message.answer(
        "Введите ФИО сотрудника для просмотра расписания:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(ScheduleStates.waiting_employee_view)

async def edit_employee_schedule_start(message: types.Message, state: FSMContext):
    """Начало редактирования расписания сотрудника"""
    user = get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer("❌ Вы не зарегистрированы. Введите /start для регистрации.")
        return
    
    await message.answer(
        "Введите ФИО сотрудника для редактирования расписания:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(ScheduleStates.waiting_employee_edit)

async def handle_user_search(message: types.Message, state: FSMContext):
    """Обработчик текстового поиска пользователей для расписания"""
    current_state = await state.get_state()
    
    search_states = [
        ScheduleStates.waiting_employee_view,
        ScheduleStates.waiting_employee_edit
    ]
    
    if current_state in [state.state for state in search_states]:
        search_query = message.text.strip()
        
        if search_query.lower() in ['отмена', 'cancel', 'отменить']:
            await state.clear()
            user = get_user_by_telegram_id(message.from_user.id)
            await message.answer(
                "❌ Поиск отменен", 
                reply_markup=get_main_keyboard(user.role.value)
            )
            return
        
        try:
            print(f"🔍 Поиск сотрудников по запросу: '{search_query}'")
            employees = search_employees_by_name(search_query)
            print(f"📊 Найдено сотрудников: {len(employees)}")
            
            if not employees:
                await message.answer(
                    f"❌ Сотрудники по запросу '{search_query}' не найдены.\n"
                    "Попробуйте ввести фамилию еще раз или введите 'отмена' для отмены:"
                )
                return
            
            kb = InlineKeyboardMarkup(inline_keyboard=[])
            
            for employee in employees:
                kb.inline_keyboard.append([
                    InlineKeyboardButton(
                        text=f"{employee.fio} ({employee.role.value})", 
                        callback_data=f"select_employee:{employee.id}"
                    )
                ])
            
            kb.inline_keyboard.append([
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_search")
            ])
            
            await message.answer(
                f"🔍 Найдено сотрудников: {len(employees)}\n"
                "Выберите сотрудника:",
                reply_markup=kb
            )
            
        except Exception as e:
            print(f"❌ Ошибка при поиске сотрудников: {e}")
            await message.answer(
                "❌ Ошибка при поиске сотрудников. Попробуйте еще раз или введите 'отмена':"
            )
    
    else:
        await message.answer("Пожалуйста, используйте кнопки меню")

async def handle_employee_selection(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора сотрудника из списка"""
    action, employee_id = callback.data.split(":")
    employee_id = int(employee_id)
    
    employee = get_user_by_id(employee_id)
    
    if action == "select_view":
        today = datetime.now().date()
        end_date = today + timedelta(days=14)
        
        schedule = get_user_schedule(employee.id, today, end_date)
        
        response = f"📅 <b>Расписание {employee.fio}:</b>\n\n"
        
        current_date = today
        while current_date <= end_date:
            day_schedule = next((s for s in schedule if s.date == current_date), None)
            
            status_emoji = {
                UserStatus.WORKING: "🟢",
                UserStatus.VACATION: "🟡",
                UserStatus.SICK_LEAVE: "🔴"
            }
            
            status = day_schedule.status if day_schedule else UserStatus.WORKING
            emoji = status_emoji.get(status, "⚪")
            status_text = get_status_text_russian(status)
            
            response += f"{emoji} <b>{current_date.strftime('%d.%m')}</b> - {status_text}\n"
            
            current_date += timedelta(days=1)
        
        await callback.message.edit_text(response, parse_mode="HTML")
        await state.clear()
        
        user = get_user_by_telegram_id(callback.from_user.id)
        await callback.message.answer(
            "-"*32,
            reply_markup=get_employee_management_keyboard()
        )
        
    elif action == "select_edit":
        await state.update_data(
            edit_employee_id=employee.id, 
            edit_employee_fio=employee.fio
        )
        
        today = datetime.now().date()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        row = []
        
        for i in range(14):
            current_date = today + timedelta(days=i)
            row.append(InlineKeyboardButton(
                text=current_date.strftime("%d.%m"),
                callback_data=f"edit_date:{current_date.strftime('%Y-%m-%d')}"
            ))
            
            if len(row) == 3:  
                keyboard.inline_keyboard.append(row)
                row = []
        
        if row:  
            keyboard.inline_keyboard.append(row)
        
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_edit")
        ])
        
        await callback.message.edit_text(
            f"Редактирование расписания для: <b>{employee.fio}</b>\n\n"
            "Выберите дату:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await state.set_state(ScheduleStates.waiting_edit_date)

async def handle_cancel_search(callback: types.CallbackQuery, state: FSMContext):
    """Отмена поиска сотрудников"""
    await state.clear()
    await callback.message.edit_text("❌ Поиск отменен")
    
    user = get_user_by_telegram_id(callback.from_user.id)
    if user.role == UserRole.MASTER:
        await callback.message.answer(
            "📅 <b>Управление расписанием</b>",
            reply_markup=get_employee_management_keyboard()
        )
    else:
        await callback.message.answer(
            "📅 <b>Мое расписание</b>", 
            reply_markup=get_schedule_keyboard()
        )

async def process_employee_schedule_view(message: types.Message, state: FSMContext):
    """Обработка поиска сотрудника для просмотра расписания"""
    if await cancel_schedule_handler(message, state):
        return
    
    search_query = message.text.strip()
    print(f"🔍 Поиск для просмотра: '{search_query}'")
    
    employees = search_employees_by_name(search_query)
    print(f"📊 Найдено сотрудников: {len(employees)}")
    
    if not employees:
        await message.answer(
            f"❌ Сотрудники по запросу '{search_query}' не найдены.\n"
            "Попробуйте ввести фамилию еще раз или введите 'отмена' для отмены:"
        )
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    
    for employee in employees:
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{employee.fio} ({employee.role.value})", 
                callback_data=f"select_view:{employee.id}"
            )
        ])
    
    kb.inline_keyboard.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_search")
    ])
    
    await message.answer(
        f"🔍 Найдено сотрудников: {len(employees)}\n"
        "Выберите сотрудника для просмотра расписания:",
        reply_markup=kb
    )

async def process_employee_edit_select(message: types.Message, state: FSMContext):
    """Обработка поиска сотрудника для редактирования расписания"""
    if await cancel_schedule_handler(message, state):
        return
    
    search_query = message.text.strip()
    print(f"🔍 Поиск для редактирования: '{search_query}'")
    
    employees = search_employees_by_name(search_query)
    print(f"📊 Найдено сотрудников: {len(employees)}")
    
    if not employees:
        await message.answer(
            f"❌ Сотрудники по запросу '{search_query}' не найдены.\n"
            "Попробуйте ввести фамилию еще раз или введите 'отмена' для отмены:"
        )
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    
    for employee in employees:
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{employee.fio} ({employee.role.value})", 
                callback_data=f"select_edit:{employee.id}"
            )
        ])
    
    kb.inline_keyboard.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_search")
    ])
    
    await message.answer(
        f"🔍 Найдено сотрудников: {len(employees)}\n"
        "Выберите сотрудника для редактирования расписания:",
        reply_markup=kb
    )

async def process_edit_date(message: types.Message, state: FSMContext):
    """Обработка даты для редактирования"""
    if message.text == "❌ Отмена":
        await state.clear()
        user = get_user_by_telegram_id(message.from_user.id)
        await message.answer("Отменено", reply_markup=get_main_keyboard(user.role.value))
        return
    
    try:
        day, month = message.text.split('.')
        year = datetime.now().year
        selected_date = datetime(year, int(month), int(day)).date()
        
        today = datetime.now().date()
        max_date = today + timedelta(days=14)
        
        if selected_date < today:
            await message.answer("❌ Нельзя редактировать прошедшие даты")
            return
        if selected_date > max_date:
            await message.answer("❌ Можно редактировать только ближайшие 2 недели")
            return
        
        await state.update_data(edit_date=selected_date)
        await message.answer(
            "Выберите новый статус:",
            reply_markup=get_status_keyboard()
        )
        await state.set_state(ScheduleStates.waiting_edit_status)
        
    except Exception as e:
        await message.answer("❌ Неверный формат даты. Используйте формат: 01.12")

async def process_edit_status(message: types.Message, state: FSMContext):
    """Обработка нового статуса для сотрудника"""
    if message.text == "❌ Отмена":
        await state.clear()
        user = get_user_by_telegram_id(message.from_user.id)
        await message.answer("Отменено", reply_markup=get_main_keyboard(user.role.value))
        return
    
    status_mapping = {
        "🟢 Работаю": UserStatus.WORKING,
        "🟡 Отпуск": UserStatus.VACATION,
        "🔴 Больничный": UserStatus.SICK_LEAVE
    }
    
    if message.text not in status_mapping:
        await message.answer("❌ Пожалуйста, выберите статус используя кнопки")
        return
    
    data = await state.get_data()
    employee_id = data['edit_employee_id']
    employee_fio = data['edit_employee_fio']
    selected_date = data['edit_date']
    status = status_mapping[message.text]
    
    set_user_schedule(employee_id, selected_date, status)
    
    await state.clear()
    
    status_emoji = {
        UserStatus.WORKING: "🟢 Работает",
        UserStatus.VACATION: "🟡 Отпуск", 
        UserStatus.SICK_LEAVE: "🔴 Больничный"
    }
    
    await message.answer(
        f"✅ <b>Расписание обновлено!</b>\n\n"
        f"👤 Сотрудник: <b>{employee_fio}</b>\n"
        f"📅 Дата: <b>{selected_date.strftime('%d.%m.%Y')}</b>\n"
        f"📊 Статус: {status_emoji[status]}",
        reply_markup=get_main_keyboard("master"),
        parse_mode="HTML"
    )

async def overall_calendar(message: types.Message):
    """Общий календарь смен на неделю"""
    user = get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer("❌ Вы не зарегистрированы. Введите /start для регистрации.")
        return
    
    today = datetime.now().date()
    end_date = today + timedelta(days=6)  
    
    from bot.database import get_all_schedules, get_all_employees
    schedules = get_all_schedules(today, end_date)
    employees = get_all_employees()
    
    response = "📊 <b>Общий календарь смен на неделю</b>\n\n"
    
    for single_date in [today + timedelta(days=i) for i in range(7)]:
        response += f"<b>📅 {single_date.strftime('%d.%m.%Y')}</b>\n"
        
        day_schedules = {s.user_id: s for s in schedules if s.date == single_date}
        
        for employee in employees:
            schedule = day_schedules.get(employee.id)
            status = schedule.status if schedule else UserStatus.WORKING
            
            status_emoji = {
                UserStatus.WORKING: "🟢",
                UserStatus.VACATION: "🟡",
                UserStatus.SICK_LEAVE: "🔴"
            }
            
            emoji = status_emoji.get(status, "⚪")
            status_text = "Работает" 
            if status == UserStatus.WORKING:
                 status_text = "Работает" 
            elif status == UserStatus.VACATION:
                status_text = "Отпуск" 
            elif status == UserStatus.SICK_LEAVE:
                status_text = "Больничный" 
            else: status.value
            
            response += f"{emoji} {employee.fio} - {status_text}\n"
        
        response += "\n"
    
    await message.answer(response, parse_mode="HTML")

async def back_to_schedule_menu(message: types.Message, state: FSMContext):
    """Возврат в меню расписания"""
    await state.clear()
    user = get_user_by_telegram_id(message.from_user.id)
    
    if user.role == UserRole.MASTER:
        await message.answer(
            "📅 <b>Управление расписанием</b>",
            reply_markup=get_employee_management_keyboard()
        )
    else:
        await message.answer(
            "📅 <b>Мое расписание</b>", 
            reply_markup=get_schedule_keyboard()
        )

async def back_to_main_menu(message: types.Message, state: FSMContext):
    """Возврат в главное меню из меню расписания"""
    await state.clear()
    user = get_user_by_telegram_id(message.from_user.id)
    await message.answer(
        "Возврат в главное меню",
        reply_markup=get_main_keyboard(user.role.value)
    )

async def debug_search(message: types.Message):
    """Функция для отладки поиска"""
    from bot.database import search_employees_by_name, get_all_employees
    
    all_users = get_all_employees()
    debug_info = "👥 Все пользователи в базе:\n\n"
    for user in all_users:
        debug_info += f"ID: {user.id}, ФИО: '{user.fio}', Роль: {user.role.value}\n"
    
    await message.answer(debug_info)
    

async def handle_edit_date_selection(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора даты для редактирования через inline кнопки"""
    date_str = callback.data.split(":")[1]
    selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    
    today = datetime.now().date()
    max_date = today + timedelta(days=14)
    
    if selected_date < today:
        await callback.answer("❌ Нельзя редактировать прошедшие даты", show_alert=True)
        return
    if selected_date > max_date:
        await callback.answer("❌ Можно редактировать только ближайшие 2 недели", show_alert=True)
        return
    
    await state.update_data(edit_date=selected_date)
    
    status_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🟢 Работаю", callback_data="edit_status:working"),
            InlineKeyboardButton(text="🟡 Отпуск", callback_data="edit_status:vacation")
        ],
        [
            InlineKeyboardButton(text="🔴 Больничный", callback_data="edit_status:sick_leave"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_edit")
        ]
    ])
    
    data = await state.get_data()
    employee_fio = data.get('edit_employee_fio', 'сотрудник')
    
    await callback.message.edit_text(
        f"Редактирование расписания для: <b>{employee_fio}</b>\n"
        f"📅 Дата: <b>{selected_date.strftime('%d.%m.%Y')}</b>\n\n"
        "Выберите новый статус:",
        reply_markup=status_keyboard,
        parse_mode="HTML"
    )
    await state.set_state(ScheduleStates.waiting_edit_status)

async def handle_edit_status_selection(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора статуса через inline кнопки"""
    status_str = callback.data.split(":")[1]
    
    status_mapping = {
        "working": UserStatus.WORKING,
        "vacation": UserStatus.VACATION,
        "sick_leave": UserStatus.SICK_LEAVE
    }
    
    status = status_mapping.get(status_str)
    if not status:
        await callback.answer("❌ Неверный статус", show_alert=True)
        return
    
    data = await state.get_data()
    employee_id = data['edit_employee_id']
    employee_fio = data['edit_employee_fio']
    selected_date = data['edit_date']
    
    set_user_schedule(employee_id, selected_date, status)
    
    await state.clear()
    
    status_emoji = {
        UserStatus.WORKING: "🟢 Работает",
        UserStatus.VACATION: "🟡 Отпуск", 
        UserStatus.SICK_LEAVE: "🔴 Больничный"
    }
    
    await callback.message.edit_text(
        f"✅ <b>Расписание обновлено!</b>\n\n"
        f"👤 Сотрудник: <b>{employee_fio}</b>\n"
        f"📅 Дата: <b>{selected_date.strftime('%d.%m.%Y')}</b>\n"
        f"📊 Статус: {status_emoji[status]}",
        parse_mode="HTML"
    )
    
    user = get_user_by_telegram_id(callback.from_user.id)
    await callback.message.answer(
        "-"*32,
        reply_markup=get_employee_management_keyboard()
    )

async def handle_cancel_edit(callback: types.CallbackQuery, state: FSMContext):
    """Отмена редактирования расписания"""
    await state.clear()
    await callback.message.edit_text("❌ Редактирование отменено")
    
    user = get_user_by_telegram_id(callback.from_user.id)
    await callback.message.answer(
        "-"*32,
        reply_markup=get_employee_management_keyboard()
    )
def register_schedule_handlers(dp: Dispatcher):
    print("🟢 DEBUG: Регистрация обработчиков расписания...")
    
    dp.message.register(schedule_main_menu, F.text == "📅 Календарь смен")
    dp.message.register(back_to_schedule_menu, F.text == "⬅️ Назад в расписание")
    
    dp.message.register(my_schedule, F.text == "📅 Мое расписание")
    dp.message.register(plan_schedule_start, F.text == "✏️ Запланировать отпуск/больничный")
    dp.message.register(back_to_main_menu, F.text == "⬅️ Назад")
    
    dp.message.register(view_employee_schedule_start, F.text == "👀 Просмотр расписания")
    dp.message.register(edit_employee_schedule_start, F.text == "✏️ Редактировать расписание")
    dp.message.register(overall_calendar, F.text == "📊 Общий календарь")
    
    print("🟢 DEBUG: Базовые обработчики зарегистрированы")
    
    dp.message.register(process_employee_schedule_view, ScheduleStates.waiting_employee_view)
    dp.message.register(process_employee_edit_select, ScheduleStates.waiting_employee_edit)
    dp.message.register(process_edit_date, ScheduleStates.waiting_edit_date)
    dp.message.register(process_edit_status, ScheduleStates.waiting_edit_status)
    dp.message.register(process_schedule_date, ScheduleStates.waiting_date)
    dp.message.register(process_schedule_status, ScheduleStates.waiting_status)
    
    print("🟢 DEBUG: Обработчики состояний зарегистрированы")
    
    dp.callback_query.register(handle_employee_selection, F.data.startswith("select_view:"))
    dp.callback_query.register(handle_employee_selection, F.data.startswith("select_edit:"))
    dp.callback_query.register(handle_edit_date_selection, F.data.startswith("edit_date:"))
    dp.callback_query.register(handle_edit_status_selection, F.data.startswith("edit_status:"))
    dp.callback_query.register(handle_cancel_search, F.data == "cancel_search")
    dp.callback_query.register(handle_cancel_edit, F.data == "cancel_edit")
    
    print("🟢 DEBUG: Инлайн обработчики зарегистрированы")
    
    dp.message.register(debug_search, F.text == "debug_search")
    
    print("🟢 DEBUG: Все обработчики расписания зарегистрированы")