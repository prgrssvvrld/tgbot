from aiogram.filters.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    waiting_fio = State()
    waiting_role = State()

class EventStates(StatesGroup):
    waiting_type = State()
    waiting_description = State()

class SearchStates(StatesGroup):
    waiting_name = State()

class ScheduleStates(StatesGroup):
    waiting_date = State()
    waiting_status = State()
    waiting_employee_view = State()
    waiting_employee_edit = State()
    waiting_edit_date = State()
    waiting_edit_status = State()