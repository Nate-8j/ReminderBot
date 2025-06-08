from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def reminder_type():
    menu = InlineKeyboardBuilder()
    menu.row(InlineKeyboardButton(
        text="разовое уведомление".encode("utf-8").decode("utf-8"),
        callback_data="one"
    ))
    menu.row(InlineKeyboardButton(
        text="регулярное напоминание".encode("utf-8").decode("utf-8"),
        callback_data="regular"
    ))
    menu.row(InlineKeyboardButton(
        text="интервальное повторение".encode("utf-8").decode("utf-8"),
        callback_data="interval"
    ))
    return menu.as_markup()


def choose_hour(call):
    hours = InlineKeyboardBuilder()
    for hour in range(24):
        hours.button(text=f"{hour:02d}", callback_data=f"{call}_{hour:02d}")
    hours.adjust(6)
    return hours.as_markup()


def choose_minute(call):
    minutes = InlineKeyboardBuilder()
    for minute in range(0, 60, 5):
        minutes.button(text=f"{minute:02d}", callback_data=f"{call}_{minute:02d}")
    minutes.adjust(6)
    return minutes.as_markup()


def type_regular_reminders():
    types = InlineKeyboardBuilder()
    types.row(InlineKeyboardButton(
        text='ежедневно',
        callback_data="regular_day"
    ))
    types.row(InlineKeyboardButton(
        text='еженедельно',
        callback_data="regular_week"
    ))
    types.row(InlineKeyboardButton(
        text='ежемесячно',
        callback_data="regular_month"
    ))
    types.row(InlineKeyboardButton(
        text='ежегодно',
        callback_data="regular_year"
    ))
    return types.as_markup()


def day_week(selected_days: set):
    kb = InlineKeyboardBuilder()

    days = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
    for i, day in enumerate(days):
        text = f"✅ {day}" if selected_days and i in selected_days else day
        kb.button(text=text, callback_data=f"week-day_{i}")

    kb.adjust(4)

    if selected_days:
        kb.row(InlineKeyboardButton(text="➡️ Дальше", callback_data="farther"))

    return kb.as_markup()


def day_of_month(tot):
    month = InlineKeyboardBuilder()

    if tot:
        for i in range(1, tot + 1):
            month.button(text=f"{i}", callback_data=f"day_{i}")
        month.adjust(7)
        return month.as_markup()

    for i in range(1, 29):
        month.button(text=f"{i}", callback_data=f"day_{i}")
    month.adjust(7)

    month.row(InlineKeyboardButton(
        text="последний день",
        callback_data="day_last"
    ))

    return month.as_markup()


def choosing_month():
    month_names = [
        "январь", "февраль", "март", "апрель", "май", "июнь",
        "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"
    ]

    kb = InlineKeyboardBuilder()

    for i, name in enumerate(month_names, start=1):
        kb.button(text=name, callback_data=f"month_{i}")

    kb.adjust(4)
    return kb.as_markup()


def delete_reminder():
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🗑 удалить", callback_data="remove_remind"))

    return kb.as_markup()
