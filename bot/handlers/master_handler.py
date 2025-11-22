from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram import Dispatcher
from aiogram.types import BufferedInputFile

from bot.database import get_events_by_date, get_user_by_telegram_id, search_employees_by_name, get_events_for_today, UserRole
from bot.keyboards import get_main_keyboard, get_cancel_keyboard, get_remove_keyboard
from bot.states import SearchStates
from bot.reports import generate_pdf_report
import datetime
import os

async def show_events_journal(message: types.Message):
    today_utc = datetime.datetime.utcnow().date()
    yesterday_utc = today_utc - datetime.timedelta(days=1)
    
    print(f"📅 Сегодня (UTC): {today_utc}, Вчера (UTC): {yesterday_utc}")
    
    events_today = get_events_for_today()  
    events_yesterday = get_events_by_date(yesterday_utc)  
    
    if not events_today and not events_yesterday:
        await message.answer("📋 За последние 2 дня событий нет")
        return
    
    response = ""
    
    if events_today:
        response += "📋 <b>События за сегодня:</b>\n\n"
        for event in events_today:
            status = "✅ Решено" if event.is_resolved else "🟡 Активно"
            event_type_emoji = {
                "STOP": "🛑",
                "BREAKDOWN": "🔧", 
                "OTHER": "📝"
            }
            
            local_time = event.timestamp + datetime.timedelta(hours=0)
            
            response += (
                f"{event_type_emoji.get(event.type.value, '📌')} <b>{local_time.strftime('%H:%M')}</b>\n"
                f"👤 <b>{event.user_fio}</b>\n" 
                f"📝 Тип: {event.type.value}\n"
                f"📋 Описание: {event.description}\n"
                f"📊 Статус: {status}\n"
                f"{'-' * 30}\n"
            )
    
    if events_yesterday:
        if response:  
            response += "\n"
        response += "📋 <b>События за вчера:</b>\n\n"
        for event in events_yesterday:
            status = "✅ Решено" if event.is_resolved else "🟡 Активно"
            event_type_emoji = {
                "STOP": "🛑",
                "BREAKDOWN": "🔧", 
                "OTHER": "📝"
            }
            
            local_time = event.timestamp + datetime.timedelta(hours=0)
            
            response += (
                f"{event_type_emoji.get(event.type.value, '📌')} <b>{local_time.strftime('%H:%M')}</b>\n"
                f"👤 <b>{event.user_fio}</b>\n" 
                f"📝 Тип: {event.type.value}\n"
                f"📋 Описание: {event.description}\n"
                f"📊 Статус: {status}\n"
                f"{'-' * 30}\n"
            )
    
    if len(response) > 4000:
        parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
        for part in parts:
            await message.answer(part, parse_mode="HTML")
    else:
        await message.answer(response, parse_mode="HTML")

async def search_employee_start(message: types.Message, state: FSMContext):
    await message.answer("Введите ФИО сотрудника для поиска:", reply_markup=get_cancel_keyboard())
    await state.set_state(SearchStates.waiting_name)

async def process_search(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        user = get_user_by_telegram_id(message.from_user.id)
        await message.answer("Поиск отменен", reply_markup=get_main_keyboard(user.role.value))
        return
    
    employees = search_employees_by_name(message.text)
    
    if employees:
        response = "👥 <b>Найденные сотрудники:</b>\n\n"
        for emp in employees:
            status_emoji = {
                "working": "🟢",
                "vacation": "🟡", 
                "sick_leave": "🔴"
            }
            role_text = "Мастер" if emp.role == UserRole.MASTER else "Сотрудник"
            
            response += (
                f"{status_emoji.get(emp.status.value, '⚪')} <b>{emp.fio}</b>\n"
                f"   🏷️ Роль: {role_text}\n"
                f"   📊 Статус: {emp.status.value}\n\n" 
            )
    else:
        response = "❌ Сотрудники не найдены"
    
    await message.answer(response, parse_mode="HTML")
    await state.clear()
    
    user = get_user_by_telegram_id(message.from_user.id)
    await message.answer("Возврат в главное меню", reply_markup=get_main_keyboard(user.role.value))

async def generate_daily_report(message: types.Message):
    await message.answer("📊 Формирую отчет за сегодня...")
    
    try:
        pdf_path = generate_pdf_report()
        
        with open(pdf_path, 'rb') as pdf_file:
            pdf_data = pdf_file.read()
        
        input_file = BufferedInputFile(
            file=pdf_data,
            filename=f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        )
        
        await message.answer_document(
            input_file,
            caption=f"📄 Отчет по событиям за {datetime.datetime.now().strftime('%d.%m.%Y')}"
        )
        
        os.remove(pdf_path)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при генерации отчета: {str(e)}")

async def show_shift_calendar(message: types.Message):
    """Перенаправляем в меню управления расписанием"""
    user = get_user_by_telegram_id(message.from_user.id)
    
    if user.role == UserRole.MASTER:
        from bot.keyboards import get_employee_management_keyboard
        await message.answer(
            "📅 <b>Управление расписанием</b>\n\n"
            "Выберите действие:",
            reply_markup=get_employee_management_keyboard(),
            parse_mode="HTML"
        )
    else:
        from bot.keyboards import get_schedule_keyboard
        await message.answer(
            "📅 <b>Мое расписание</b>\n\n"
            "Выберите действие:",
            reply_markup=get_schedule_keyboard(),
            parse_mode="HTML"
        )

async def show_my_status(message: types.Message):
    user = get_user_by_telegram_id(message.from_user.id)
    
    status_emoji = {
        "working": "🟢 Работает",
        "vacation": "🟡 Отпуск", 
        "sick_leave": "🔴 Больничный"
    }
    
    role_text = "Мастер" if user.role == UserRole.MASTER else "Сотрудник"
    
    await message.answer(
        f"👤 <b>Ваш статус:</b>\n\n"
        f"🏷️ ФИО: <b>{user.fio}</b>\n"
        f"🎯 Роль: <b>{role_text}</b>\n"
        f"📊 Статус: <b>{status_emoji.get(user.status.value, '⚪ Неизвестно')}</b>",
        parse_mode="HTML"
    )

def register_master_handlers(dp: Dispatcher):
    dp.message.register(show_events_journal, F.text == "📋 Журнал событий")
    dp.message.register(search_employee_start, F.text == "👥 Поиск сотрудника")
    dp.message.register(generate_daily_report, F.text == "📄 Отчет за день")
    dp.message.register(show_shift_calendar, F.text == "📅 Календарь смен")
    dp.message.register(show_my_status, F.text == "ℹ️ Мой статус")
    dp.message.register(process_search, SearchStates.waiting_name)