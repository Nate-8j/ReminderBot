from aiogram.fsm.state import StatesGroup, State


class OneTimeStt(StatesGroup):
    date = State()
    hour = State()
    minute = State()
    txt = State()
    message_id = State()


class RegularStt(StatesGroup):
    my_types = State()
    day = State()
    weekday = State()
    month = State()
    hour = State()
    minute = State()
    txt = State()
    message_id = State()


class ListStt(StatesGroup):
    txt = State()
    reminder_seq = State()
