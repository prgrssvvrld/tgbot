from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Enum, Text, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import enum

from config import DATABASE_URL

Base = declarative_base()

class UserRole(enum.Enum):
    EMPLOYEE = "employee"
    MASTER = "master"

class UserStatus(enum.Enum):
    WORKING = "working"
    VACATION = "vacation"
    SICK_LEAVE = "sick_leave"

class EventType(enum.Enum):
    BREAKDOWN = "breakdown"
    STOP = "stop"
    OTHER = "other"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    fio = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.EMPLOYEE)
    shift = Column(String(50), default="Смена 1")
    status = Column(Enum(UserStatus), default=UserStatus.WORKING)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    user_fio = Column(String(100), nullable=False)
    type = Column(Enum(EventType), nullable=False)
    description = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    is_resolved = Column(Boolean, default=False)

class UserSchedule(Base):
    __tablename__ = 'user_schedule'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    status = Column(Enum(UserStatus), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

engine = create_engine(DATABASE_URL.replace("+aiosqlite", ""), echo=True)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    print("База данных инициализирована")

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

def create_user(telegram_id: int, fio: str, role: UserRole = UserRole.EMPLOYEE, shift: str = "Смена 1"):
    db = get_db()
    user = User(telegram_id=telegram_id, fio=fio, role=role, shift=shift)
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user

def get_user_by_telegram_id(telegram_id: int):
    db = get_db()
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    db.close()
    return user

def get_user_by_id(user_id: int):
    """Получить пользователя по ID"""
    db = get_db()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        return user
    finally:
        db.close()

def get_all_masters():
    db = get_db()
    masters = db.query(User).filter(User.role == UserRole.MASTER).all()
    db.close()
    return masters

def get_all_employees():
    db = get_db()
    employees = db.query(User).all()
    db.close()
    return employees

def create_event(user_id: int, user_fio: str, event_type: EventType, description: str):
    db = get_db()
    event = Event(
        user_id=user_id,
        user_fio=user_fio,
        type=event_type,
        description=description
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    db.close()
    return event

def get_events_for_today():
    db = get_db()
    
    today_utc = datetime.datetime.utcnow().date()
    
    print(f"🔍 Поиск событий за сегодня ({today_utc} UTC)")
    
    start_of_day = datetime.datetime.combine(today_utc, datetime.time.min)
    end_of_day = datetime.datetime.combine(today_utc, datetime.time.max)
    
    events = db.query(Event).filter(
        Event.timestamp >= start_of_day,
        Event.timestamp <= end_of_day
    ).order_by(Event.timestamp.desc()).all()
    
    print(f"📊 Найдено событий за сегодня: {len(events)}")
    
    db.close()
    return events

def get_events_by_date(target_date: datetime.date):
    """Получает события за конкретную дату (в UTC)"""
    db = get_db()
    
    print(f"🔍 Поиск событий за {target_date} (UTC)")
    
    start_of_day = datetime.datetime.combine(target_date, datetime.time.min)
    end_of_day = datetime.datetime.combine(target_date, datetime.time.max)
    
    events = db.query(Event).filter(
        Event.timestamp >= start_of_day,
        Event.timestamp <= end_of_day
    ).order_by(Event.timestamp.desc()).all()
    
    print(f"📊 Найдено событий за {target_date}: {len(events)}")
    
    db.close()
    return events

def search_users_by_name(name_query: str):
    """Поиск пользователей по имени"""
    db = get_db()
    try:
        users = db.query(User).filter(
            User.fio.ilike(f"%{name_query}%")
        ).all()
        return users
    finally:
        db.close()

def search_employees_by_name(name_query: str):
    """Поиск сотрудников по имени"""
    db = get_db()
    try:
        employees = db.query(User).filter(
            User.fio.ilike(f"%{name_query}%")
        ).all()
        return employees
    finally:
        db.close()

def set_user_schedule(user_id: int, date: datetime.date, status: UserStatus):
    db = get_db()
    
    db.query(UserSchedule).filter(
        UserSchedule.user_id == user_id,
        UserSchedule.date == date
    ).delete()
    
    schedule = UserSchedule(
        user_id=user_id,
        date=date,
        status=status
    )
    db.add(schedule)
    db.commit()
    db.close()

def get_user_schedule(user_id: int, start_date: datetime.date, end_date: datetime.date):
    db = get_db()
    schedule = db.query(UserSchedule).filter(
        UserSchedule.user_id == user_id,
        UserSchedule.date >= start_date,
        UserSchedule.date <= end_date
    ).all()
    db.close()
    return schedule

def get_all_schedules(start_date: datetime.date, end_date: datetime.date):
    db = get_db()
    schedules = db.query(UserSchedule).filter(
        UserSchedule.date >= start_date,
        UserSchedule.date <= end_date
    ).all()
    db.close()
    return schedules