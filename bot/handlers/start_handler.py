from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram import Dispatcher
from aiogram.filters import Command

from bot.database import get_user_by_telegram_id, create_user, UserRole
from bot.keyboards import get_main_keyboard, get_remove_keyboard, get_role_keyboard
from bot.states import RegistrationStates

async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    
    user = get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer("👋 Добро пожаловать в систему РУСАЛ-Смена!\n\nВведите ваше ФИО:")
        await state.set_state(RegistrationStates.waiting_fio)
    else:
        role_name = "мастер" if user.role == UserRole.MASTER else "сотрудник"
        await message.answer(
            f"✅ Вы авторизованы как <b>{user.fio}</b>\n"
            f"🏷️ Роль: {role_name}",  
            reply_markup=get_main_keyboard(user.role.value),
            parse_mode="HTML"
        )

async def process_fio(message: types.Message, state: FSMContext):
    await state.update_data(fio=message.text)
    await message.answer(
        "Выберите вашу роль:",
        reply_markup=get_role_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_role)

async def process_role(message: types.Message, state: FSMContext):
    if message.text not in ["👨‍💼 Сотрудник", "👨‍🏭 Мастер смены"]:
        await message.answer("Пожалуйста, выберите роль используя кнопки:")
        return
    
    data = await state.get_data()
    fio = data['fio']
    
    role = UserRole.MASTER if message.text == "👨‍🏭 Мастер смены" else UserRole.EMPLOYEE
    
    user = create_user(
        telegram_id=message.from_user.id,
        fio=fio,
        role=role
    )
    
    await state.clear()
    role_name = "мастер" if role == UserRole.MASTER else "сотрудник"
    await message.answer(
        f"✅ <b>Регистрация завершена!</b>\n\n"
        f"👤 Добро пожаловать, <b>{user.fio}</b>!\n"
        f"🏷️ Ваша роль: <b>{role_name}</b>",  
        reply_markup=get_main_keyboard(user.role.value),
        parse_mode="HTML"
    )


def register_start_handlers(dp: Dispatcher):
    dp.message.register(start_handler, Command("start"))
    dp.message.register(process_fio, RegistrationStates.waiting_fio)
    dp.message.register(process_role, RegistrationStates.waiting_role)