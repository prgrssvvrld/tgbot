from .start_handler import register_start_handlers
from .event_handler import register_event_handlers
from .master_handler import register_master_handlers
from .schedule_handler import register_schedule_handlers  

def register_all_handlers(dp):
    register_start_handlers(dp)
    register_event_handlers(dp)
    register_master_handlers(dp)
    register_schedule_handlers(dp)  