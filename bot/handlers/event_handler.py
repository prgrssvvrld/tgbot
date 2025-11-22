from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram import Dispatcher

from bot.database import get_user_by_telegram_id, create_event, EventType, get_all_masters
from bot.keyboards import get_main_keyboard, get_event_type_keyboard, get_cancel_keyboard, get_remove_keyboard
from bot.states import EventStates
import datetime

async def create_event_start(message: types.Message, state: FSMContext):
    await message.answer("Выберите тип события:", reply_markup=get_event_type_keyboard())
    await state.set_state(EventStates.waiting_type)

async def process_event_type(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        user = get_user_by_telegram_id(message.from_user.id)
        await message.answer("Создание события отменено", reply_markup=get_main_keyboard(user.role.value))
        return
    
    type_mapping = {
        "🛑 Остановка оборудования": EventType.STOP,
        "🔧 Поломка": EventType.BREAKDOWN,
        "📝 Другое": EventType.OTHER
    }
    
    event_type = type_mapping.get(message.text, EventType.OTHER)
    
    await state.update_data(event_type=event_type)
    await message.answer("Опишите проблему подробно:", reply_markup=get_cancel_keyboard())
    await state.set_state(EventStates.waiting_description)

async def process_event_description(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        user = get_user_by_telegram_id(message.from_user.id)
        await message.answer("Создание события отменено", reply_markup=get_main_keyboard(user.role.value))
        return
    
    user = get_user_by_telegram_id(message.from_user.id)
    data = await state.get_data()
    
    event = create_event(
        user_id=user.id,
        user_fio=user.fio,
        event_type=data['event_type'],
        description=message.text
    )
    
    await notify_masters(message.bot, data['event_type'], message.text, user.fio)
    
    await state.clear()
    await message.answer(
        "✅ <b>Событие успешно зарегистрировано!</b>\n\n"
        f"📋 Тип: {data['event_type'].value}\n"
        f"📝 Описание: {message.text}",
        reply_markup=get_main_keyboard(user.role.value),
        parse_mode="HTML"
    )

async def notify_masters(bot, event_type: EventType, description: str, user_fio: str):
    masters = get_all_masters()
    
    event_type_text = {
        EventType.STOP: "🛑 ОСТАНОВКА ОБОРУДОВАНИЯ",
        EventType.BREAKDOWN: "🔧 ПОЛОМКА", 
        EventType.OTHER: "📝 ДРУГОЕ СОБЫТИЕ"
    }
    
    message_text = (
        f"🚨 <b>НОВОЕ ПРОИЗВОДСТВЕННОЕ СОБЫТИЕ</b>\n\n"
        f"📋 Тип: {event_type_text[event_type]}\n"
        f"👤 Сотрудник: {user_fio}\n"
        f"📝 Описание: {description}\n"
        f"🕒 Время: {datetime.datetime.now().strftime('%H:%M %d.%m.%Y')}"
    )
    
    for master in masters:
        try:
            await bot.send_message(
                master.telegram_id, 
                message_text,
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Ошибка отправки уведомления мастеру {master.fio}: {e}")

def register_event_handlers(dp: Dispatcher):
    dp.message.register(create_event_start, F.text == "📊 Создать событие")
    dp.message.register(process_event_type, EventStates.waiting_type)
    dp.message.register(process_event_description, EventStates.waiting_description)