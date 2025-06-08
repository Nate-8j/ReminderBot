<<<<<<< HEAD
import calendar
from datetime import datetime, timedelta

from aiogram import types, F, Router
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery
from apscheduler.triggers.cron import CronTrigger

from config import reminder_manager, bot, repository
from kbds import inline, reply

from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback

usr_prv = Router()


class Stt(StatesGroup):
    date = State()
    hour = State()
    minute = State()
    txt = State()
    message_id = State()


@usr_prv.message(CommandStart())
async def starting_message(message: types.Message):
    start_text = await repository.get_text_from_db('start_text')
    await message.answer(start_text, reply_markup=reply.add_kb)


@usr_prv.message(Command('help'))
async def command_help(message: types.Message):
    text = await repository.get_text_from_db('command_help')
    await message.answer(text, parse_mode="HTML")


@usr_prv.message(Command('interval_reminders'))
async def help_interval_reminders(message: types.Message):
    text = await repository.get_text_from_db('interval_reminders')
    await message.answer(text, parse_mode="HTML")


@usr_prv.message(Command('examples'))
async def examples(message: types.Message):
    text = await repository.get_text_from_db('examples')
    await message.answer(text, parse_mode="HTML")


######### 1) разовое 2) регулярное 3) интервальное
@usr_prv.message(F.text.lower() == "добавить")
@usr_prv.message(Command('new'))
async def add_reminder_type(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Выберите тип", reply_markup=inline.reminder_type())


########################################################################################################################
""" Разовое уведомление """


@usr_prv.callback_query(StateFilter(None), F.data == "one")
async def onetime_nav_cal_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Пожалуйста выберите дату: ",
        reply_markup=await SimpleCalendar(locale='ru_RU.UTF-8').start_calendar()
    )
    await state.set_state(Stt.date)


@usr_prv.callback_query(SimpleCalendarCallback.filter(), Stt.date)
async def onetime_calendar(callback_query: CallbackQuery, callback_data, state: FSMContext):
    mypy_calendar = SimpleCalendar(locale='ru_RU.UTF-8')
    mypy_calendar.set_dates_range(datetime(2025, 1, 1), datetime(2028, 12, 31))
    selected, date = await mypy_calendar.process_selection(callback_query, callback_data)
    if selected:
        await state.update_data(
            year=date.year,
            month=date.month,
            day=date.day
        )
        await state.set_state(Stt.hour)
        await callback_query.message.edit_text(
            "Выберите час: ",
            reply_markup=inline.choose_hour('one-h')
        )

        await callback_query.answer()


@usr_prv.callback_query(F.data.startswith('one-h'), Stt.hour)
async def onetime_hour(callback: types.CallbackQuery, state: FSMContext):
    hour = int(callback.data.split('_')[-1])
    await state.update_data(hour=hour)
    await state.set_state(Stt.minute)
    await callback.message.edit_text(
        "Выберите минуты: ",
        reply_markup=inline.choose_minute('one-m')
    )
    await callback.answer()


@usr_prv.callback_query(F.data.startswith('one-m'), Stt.minute)
async def onetime_minute(callback: CallbackQuery, state: FSMContext):
    minute = int(callback.data.split('_')[-1])
    await state.update_data(
        minute=minute,
        message_id=callback.message.message_id
    )
    await state.set_state(Stt.txt)
    await callback.message.edit_text(
        f"Введите текст напоминания"
    )
    await callback.answer()


@usr_prv.message(Stt.txt)
async def onetime_txt(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Введите текст!")
        return

    await message.delete()

    data = await state.get_data()
    remind_date = datetime(
        year=data['year'],
        month=data['month'],
        day=data['day'],
        hour=data['hour'],
        minute=data['minute']
    )
    txt = message.text
    small_text = txt if len(txt) < 15 else txt[:15] + '...'
    time_ = str(remind_date.strftime('%d.%m.%Y %H:%M'))

    job_id = await reminder_manager.add_onetime_reminder(chat_id=message.chat.id, text=txt, remind_time=remind_date)
    await repository.add_reminder(chat_id=message.chat.id, job_id=job_id, text=small_text, type_='раз.', time_next_reminder=time_)

    formatted_text = (
        f"✅ <b>Напоминание установлено</b>\n"
        f"📅 <i>{remind_date.strftime('%d.%m.%Y %H:%M')}</i>"
    )

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=data['message_id'],
        text=formatted_text,
        parse_mode="HTML"
    )
    await state.clear()


########################################################################################################################
""" Регулярные напоминания"""


class RegularStt(StatesGroup):
    my_types = State()
    day = State()
    weekday = State()
    month = State()
    hour = State()
    minute = State()
    txt = State()
    message_id = State()


@usr_prv.callback_query(StateFilter(None), F.data == "regular")
async def regular(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(RegularStt.my_types)
    await callback.message.edit_text(
        "Выберете тип: ",
        reply_markup=inline.type_regular_reminders()
    )
    await callback.answer()


@usr_prv.callback_query(RegularStt.my_types, F.data == "regular_year")
async def annual_reminders(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(my_types="year")
    await state.set_state(RegularStt.month)
    await callback.message.edit_text(
        text='Выберите месяц:',
        reply_markup=inline.choosing_month()
    )
    await callback.answer()


@usr_prv.callback_query(RegularStt.month, F.data.startswith('month_'))
async def day_of_month(callback: types.CallbackQuery, state: FSMContext):
    month = int(callback.data.split('_')[-1])
    total = calendar.monthrange(year=datetime.now().year, month=month)[1]
    await state.update_data(month=month)
    await state.set_state(RegularStt.day)
    await callback.message.edit_text(
        text='Выберите день:',
        reply_markup=inline.day_of_month(total)
    )
    await callback.answer()


@usr_prv.callback_query(RegularStt.my_types, F.data == "regular_month")
async def monthly_reminders(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(my_types="month")
    await state.set_state(RegularStt.day)
    await callback.message.edit_text(
        text='Выберите день:',
        reply_markup=inline.day_of_month(None)
    )
    await callback.answer()


@usr_prv.callback_query(RegularStt.my_types, F.data == "regular_week")
async def weekly_reminders(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_weekdays = data.get("selected_weekdays", set())

    await state.update_data(my_types="week")
    await state.set_state(RegularStt.weekday)
    await callback.message.edit_text(
        text='Выберите день:',
        reply_markup=inline.day_week(selected_weekdays),
    )

    await callback.answer()


@usr_prv.callback_query(RegularStt.weekday, F.data.startswith("week-day"))
async def selected_weekday(callback: types.CallbackQuery, state: FSMContext):
    day_index = int(callback.data.split('_')[-1])

    data = await state.get_data()
    selected_weekdays = data.get('selected_weekdays', set())

    if day_index in selected_weekdays:
        selected_weekdays.discard(day_index)
    else:
        selected_weekdays.add(day_index)

    await state.update_data(selected_weekdays=selected_weekdays)

    await callback.message.edit_reply_markup(
        reply_markup=inline.day_week(selected_weekdays)
    )


@usr_prv.callback_query(F.data.startswith("day"), RegularStt.day)
@usr_prv.callback_query(F.data == "farther")
@usr_prv.callback_query(F.data == "regular_day")
async def hours_for_regular(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if data.get("my_types") == "month" or data.get("my_types") == "year":
        await state.update_data(day=callback.data.split('_')[-1])

    await state.set_state(RegularStt.hour)
    await callback.message.edit_text(
        text='Выберите час:',
        reply_markup=inline.choose_hour('regular-day-h')
    )
    await callback.answer()


@usr_prv.callback_query(RegularStt.hour, F.data.startswith("regular-day-h"))
async def minute_for_regula(callback: types.CallbackQuery, state: FSMContext):
    hour = int(callback.data.split('_')[-1])
    await state.update_data(hour=hour)
    await state.set_state(RegularStt.minute)

    await callback.message.edit_text(
        text='Выберите минуту:',
        reply_markup=inline.choose_minute('regular-day-m')
    )
    await callback.answer()


@usr_prv.callback_query(RegularStt.minute, F.data.startswith("regular-day-m"))
async def txt_for_regular(callback: types.CallbackQuery, state: FSMContext):
    minute = int(callback.data.split('_')[-1])
    await state.update_data(minute=minute)
    await state.update_data(message_id=callback.message.message_id)
    await state.set_state(RegularStt.txt)

    await callback.message.edit_text(
        text="Введите текст напоминания:"
    )
    await callback.answer()


@usr_prv.message(RegularStt.txt)
async def saving_regular(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Введите текст!")
        return

    await message.delete()

    data = await state.get_data()

    my_types = data.get('my_types')
    chat_id = message.chat.id
    txt = message.text
    day = data.get('day')
    selected_weekdays = data.get("selected_weekdays")
    hour = data.get('hour')
    minute = data.get('minute')
    month = data.get('month')

    message_id = data.get('message_id')
    small_text = txt if len(txt) < 15 else txt[:15] + '...'
    week_day_text = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]

    trigger = None
    time_ = None

    if not my_types:
        trigger = CronTrigger(hour=hour, minute=minute)
        time_ = f'{hour}:{minute}'

    elif my_types == "week":
        days_digit = ",".join(str(day) for day in selected_weekdays)
        days_str = [week_day_text[int(i)] for i in days_digit.split(',')]
        trigger = CronTrigger(day_of_week=days_digit, hour=hour, minute=minute)
        time_ = f'{", ".join(days_str)} {hour}:{minute}'

    elif my_types == "month":
        trigger = CronTrigger(day=day, hour=hour, minute=minute)
        time_ = f'{day} {hour}:{minute}'

    elif my_types == "year":
        trigger = CronTrigger(month=month, day=day, hour=hour, minute=minute)
        time_ = f'{month} {day} {hour}:{minute}'

    job_id = await reminder_manager.add_regular_reminder(chat_id=chat_id, text=txt, trigger=trigger)
    await repository.add_reminder(chat_id=chat_id, job_id=job_id, text=small_text, type_='рег.', time_next_reminder=time_)

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message_id,
        text="✅ <b>Напоминание установлено</b>",
        parse_mode="HTML"
    )
    await state.clear()


########################################################################################################################
""" Интервальные повторения """


class IntervalStt(StatesGroup):
    hour = State()
    minute = State()
    txt = State()
    message_id = State()


@usr_prv.callback_query(StateFilter(None), F.data == "interval")
async def interval(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(IntervalStt.hour)

    await callback.message.edit_text(
        text="Выберите час:",
        reply_markup=inline.choose_hour('interval-h')
    )
    await callback.answer()


@usr_prv.callback_query(IntervalStt.hour, F.data.startswith("interval-h"))
async def interval(callback: types.CallbackQuery, state: FSMContext):
    hour = int(callback.data.split('_')[-1])
    await state.update_data(hour=hour)
    await state.set_state(IntervalStt.minute)

    await callback.message.edit_text(
        text="Выберите минуту:",
        reply_markup=inline.choose_minute('interval-m')
    )
    await callback.answer()


@usr_prv.callback_query(IntervalStt.minute, F.data.startswith("interval-m"))
async def interval_txt(callback: types.CallbackQuery, state: FSMContext):
    minute = int(callback.data.split('_')[-1])
    await state.update_data(minute=minute)
    await state.update_data(message_id=callback.message.message_id)
    await state.set_state(IntervalStt.txt)

    await callback.message.edit_text(
        text="Введите текст для напоминаний"
    )
    await callback.answer()


@usr_prv.message(IntervalStt.txt)
async def interval_save(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Введите текст!")
        return
    await message.delete()
    intervals = [
        timedelta(days=1),
        timedelta(days=3),
        timedelta(days=7),
        timedelta(days=16),
        timedelta(days=35),
        timedelta(days=90),
        timedelta(days=180),
        timedelta(days=365)
    ]

    data = await state.get_data()
    hour = data.get("hour")
    minute = data.get("minute")
    message_id = data.get("message_id")
    chat_id = message.chat.id
    txt = message.text
    small_text = txt if len(txt) < 15 else txt[:15] + '...'
    reminder_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)

    for delta in intervals:
        scheduled_time = reminder_time + delta
        time_ = str(scheduled_time)

        job_id = await reminder_manager.add_interval_repetition(chat_id=chat_id, text=txt, remind_time=scheduled_time)
        await repository.add_reminder(chat_id=chat_id, job_id=job_id, text=small_text, type_='инт', time_next_reminder=time_)

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message_id,
        text="✅ <b>готово!</b>\n",
        parse_mode="HTML"
    )
    await state.clear()


########################################################################################################################

class ListStt(StatesGroup):
    txt = State()


@usr_prv.message(F.text.lower() == "список")
@usr_prv.message(Command('list'))
async def list_reminders(message: types.Message, state: FSMContext):
    await state.clear()

    reminders_from_users = await repository.get_reminder(chat_id=message.chat.id)
    active_reminders = await reminder_manager.scheduler.get_schedules()

    db_job_ids = {row.get('job_id') for row in reminders_from_users}
    active_job_ids = {job.id for job in active_reminders}

    to_delete = db_job_ids - active_job_ids
    if to_delete:
        await repository.delete_not_active_reminders(to_delete)

    res_reminders = [row for row in reminders_from_users if row.get('job_id') in active_job_ids]
    if not res_reminders:
        await message.answer("❌ У вас нет активных напоминаний.")
        return

    text = f"<b>ваши активные напоминания:</b>\n"
    for i, reminder in enumerate(res_reminders):
        txt = reminder.get('text')
        type_ = reminder.get('type')
        time_ = reminder.get('time_reminder')
        if txt not in text:
            text += f"{i + 1}) <i>{txt}</i>  -  {time_} ({type_})\n"

    await message.answer(
        text=text,
        reply_markup=inline.delete_reminder(),
        parse_mode="HTML"
    )


@usr_prv.callback_query(F.data == "remove_remind", StateFilter(None))
async def remove_remind(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(text="введите номер(а) через пробелы")
    await state.set_state(ListStt.txt)


@usr_prv.message(ListStt.txt)
async def remove_r(message: types.Message, state: FSMContext):
    reminder_list = await repository.get_reminder(chat_id=message.chat.id)
    try:
        indices = [int(x) for x in message.text.split()]
    except ValueError:
        await message.answer("❌ Введите корректные номера через пробелы")
        return
    await state.clear()
    deleted = []
    for idx in indices:
        if 1 <= idx <= len(reminder_list):
            job_id = reminder_list[idx - 1].get('job_id')

            ### выбираю все инт напоминания чтобы не выводить 10 одинаковых
            txt = reminder_list[idx - 1].get('text')
            if reminder_list[idx - 1].get('type') == 'инт.':
                for reminder in reminder_list:
                    if reminder.get('type') == 'инт.' and reminder.get('text') == txt:
                        job_id_ = reminder.get('job_id')

                        await repository.delete_reminder(job_id=job_id_)
                        await reminder_manager.scheduler.remove_schedule(job_id_)

            else:
                await repository.delete_reminder(job_id=job_id)
                await reminder_manager.scheduler.remove_schedule(job_id)

            deleted.append(idx)
    if deleted:
        await message.answer(f"✅ Готово: {', '.join(map(str, deleted))}")
    else:
        await message.answer("❌ Попробуйте снова")
        return
=======
import calendar
from datetime import datetime, timedelta

from aiogram import types, F, Router
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery
from apscheduler.triggers.cron import CronTrigger

from config import reminder_manager, bot, repository
from kbds import inline, reply

from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback

usr_prv = Router()


class Stt(StatesGroup):
    date = State()
    hour = State()
    minute = State()
    txt = State()
    message_id = State()


@usr_prv.message(CommandStart())
async def starting_message(message: types.Message):
    start_text = await repository.get_text_from_db('start_text')
    await message.answer(start_text, reply_markup=reply.add_kb)


@usr_prv.message(Command('help'))
async def command_help(message: types.Message):
    text = await repository.get_text_from_db('command_help')
    await message.answer(text, parse_mode="HTML")


@usr_prv.message(Command('interval_reminders'))
async def help_interval_reminders(message: types.Message):
    text = await repository.get_text_from_db('interval_reminders')
    await message.answer(text, parse_mode="HTML")


@usr_prv.message(Command('examples'))
async def examples(message: types.Message):
    text = await repository.get_text_from_db('examples')
    await message.answer(text, parse_mode="HTML")


######### 1) разовое 2) регулярное 3) интервальное
@usr_prv.message(F.text.lower() == "добавить")
@usr_prv.message(Command('new'))
async def add_reminder_type(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Выберите тип", reply_markup=inline.reminder_type())


########################################################################################################################
""" Разовое уведомление """


@usr_prv.callback_query(StateFilter(None), F.data == "one")
async def onetime_nav_cal_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Пожалуйста выберите дату: ",
        reply_markup=await SimpleCalendar().start_calendar()  # locale='ru_RU.UTF-8'
    )
    await state.set_state(Stt.date)


@usr_prv.callback_query(SimpleCalendarCallback.filter(), Stt.date)
async def onetime_calendar(callback_query: CallbackQuery, callback_data, state: FSMContext):
    mypy_calendar = SimpleCalendar()  # locale='ru_RU.UTF-8'
    mypy_calendar.set_dates_range(datetime(2025, 1, 1), datetime(2028, 12, 31))
    selected, date = await mypy_calendar.process_selection(callback_query, callback_data)
    if selected:
        await state.update_data(
            year=date.year,
            month=date.month,
            day=date.day
        )
        await state.set_state(Stt.hour)
        await callback_query.message.edit_text(
            "Выберите час: ",
            reply_markup=inline.choose_hour('one-h')
        )

        await callback_query.answer()


@usr_prv.callback_query(F.data.startswith('one-h'), Stt.hour)
async def onetime_hour(callback: types.CallbackQuery, state: FSMContext):
    hour = int(callback.data.split('_')[-1])
    await state.update_data(hour=hour)
    await state.set_state(Stt.minute)
    await callback.message.edit_text(
        "Выберите минуты: ",
        reply_markup=inline.choose_minute('one-m')
    )
    await callback.answer()


@usr_prv.callback_query(F.data.startswith('one-m'), Stt.minute)
async def onetime_minute(callback: CallbackQuery, state: FSMContext):
    minute = int(callback.data.split('_')[-1])
    await state.update_data(
        minute=minute,
        message_id=callback.message.message_id
    )
    await state.set_state(Stt.txt)
    await callback.message.edit_text(
        f"Введите текст напоминания"
    )
    await callback.answer()


@usr_prv.message(Stt.txt)
async def onetime_txt(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Введите текст!")
        return
    await message.delete()

    data = await state.get_data()
    remind_date = datetime(
        year=data['year'],
        month=data['month'],
        day=data['day'],
        hour=data['hour'],
        minute=data['minute']
    )
    txt = message.text
    small_text = txt if len(txt) < 15 else txt[:15] + '...'
    time_ = str(remind_date.strftime('%d.%m.%Y %H:%M'))

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=data['message_id'],
        text="🕓 добавляю...",
        parse_mode="HTML"
    )

    await reminder_manager.add_onetime_reminder(
        chat_id=message.chat.id,
        text=txt,
        remind_time=remind_date,
        small_text=small_text,
        type_='раз.',
        time_next_reminder=time_
    )
    formatted_text = (
        f"✅ <b>Напоминание установлено</b>\n"
        f"📅 <i>{remind_date.strftime('%d.%m.%Y %H:%M')}</i>"
    )

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=data['message_id'],
        text=formatted_text,
        parse_mode="HTML"
    )
    await state.clear()


########################################################################################################################
""" Регулярные напоминания"""


class RegularStt(StatesGroup):
    my_types = State()
    day = State()
    weekday = State()
    month = State()
    hour = State()
    minute = State()
    txt = State()
    message_id = State()


@usr_prv.callback_query(StateFilter(None), F.data == "regular")
async def regular(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(RegularStt.my_types)
    await callback.message.edit_text(
        "Выберете тип: ",
        reply_markup=inline.type_regular_reminders()
    )
    await callback.answer()


@usr_prv.callback_query(RegularStt.my_types, F.data == "regular_year")
async def annual_reminders(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(my_types="year")
    await state.set_state(RegularStt.month)
    await callback.message.edit_text(
        text='Выберите месяц:',
        reply_markup=inline.choosing_month()
    )
    await callback.answer()


@usr_prv.callback_query(RegularStt.month, F.data.startswith('month_'))
async def day_of_month(callback: types.CallbackQuery, state: FSMContext):
    month = int(callback.data.split('_')[-1])
    total = calendar.monthrange(year=datetime.now().year, month=month)[1]
    await state.update_data(month=month)
    await state.set_state(RegularStt.day)
    await callback.message.edit_text(
        text='Выберите день:',
        reply_markup=inline.day_of_month(total)
    )
    await callback.answer()


@usr_prv.callback_query(RegularStt.my_types, F.data == "regular_month")
async def monthly_reminders(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(my_types="month")
    await state.set_state(RegularStt.day)
    await callback.message.edit_text(
        text='Выберите день:',
        reply_markup=inline.day_of_month(None)
    )
    await callback.answer()


@usr_prv.callback_query(RegularStt.my_types, F.data == "regular_week")
async def weekly_reminders(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_weekdays = data.get("selected_weekdays", set())

    await state.update_data(my_types="week")
    await state.set_state(RegularStt.weekday)
    await callback.message.edit_text(
        text='Выберите день:',
        reply_markup=inline.day_week(selected_weekdays),
    )

    await callback.answer()


@usr_prv.callback_query(RegularStt.weekday, F.data.startswith("week-day"))
async def selected_weekday(callback: types.CallbackQuery, state: FSMContext):
    day_index = int(callback.data.split('_')[-1])

    data = await state.get_data()
    selected_weekdays = data.get('selected_weekdays', set())

    if day_index in selected_weekdays:
        selected_weekdays.discard(day_index)
    else:
        selected_weekdays.add(day_index)

    await state.update_data(selected_weekdays=selected_weekdays)

    await callback.message.edit_reply_markup(
        reply_markup=inline.day_week(selected_weekdays)
    )


@usr_prv.callback_query(F.data.startswith("day"), RegularStt.day)
@usr_prv.callback_query(F.data == "farther")
@usr_prv.callback_query(F.data == "regular_day")
async def hours_for_regular(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if data.get("my_types") == "month" or data.get("my_types") == "year":
        await state.update_data(day=callback.data.split('_')[-1])

    await state.set_state(RegularStt.hour)
    await callback.message.edit_text(
        text='Выберите час:',
        reply_markup=inline.choose_hour('regular-day-h')
    )
    await callback.answer()


@usr_prv.callback_query(RegularStt.hour, F.data.startswith("regular-day-h"))
async def minute_for_regula(callback: types.CallbackQuery, state: FSMContext):
    hour = int(callback.data.split('_')[-1])
    await state.update_data(hour=hour)
    await state.set_state(RegularStt.minute)

    await callback.message.edit_text(
        text='Выберите минуту:',
        reply_markup=inline.choose_minute('regular-day-m')
    )
    await callback.answer()


@usr_prv.callback_query(RegularStt.minute, F.data.startswith("regular-day-m"))
async def txt_for_regular(callback: types.CallbackQuery, state: FSMContext):
    minute = int(callback.data.split('_')[-1])
    await state.update_data(minute=minute)
    await state.update_data(message_id=callback.message.message_id)
    await state.set_state(RegularStt.txt)

    await callback.message.edit_text(
        text="Введите текст напоминания:"
    )
    await callback.answer()


@usr_prv.message(RegularStt.txt)
async def saving_regular(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Введите текст!")
        return

    await message.delete()

    data = await state.get_data()

    my_types = data.get('my_types')
    chat_id = message.chat.id
    txt = message.text
    day = data.get('day')
    selected_weekdays = data.get("selected_weekdays")
    hour = data.get('hour')
    minute = data.get('minute')
    month = data.get('month')

    message_id = data.get('message_id')
    small_text = txt if len(txt) < 15 else txt[:15] + '...'
    week_day_text = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]

    trigger = None
    time_ = None

    if not my_types:
        trigger = CronTrigger(hour=hour, minute=minute)
        time_ = f'{hour}:{minute}'

    elif my_types == "week":
        days_digit = ",".join(str(day) for day in selected_weekdays)
        days_str = [week_day_text[int(i)] for i in days_digit.split(',')]
        trigger = CronTrigger(day_of_week=days_digit, hour=hour, minute=minute)
        time_ = f'{", ".join(days_str)} {hour}:{minute}'

    elif my_types == "month":
        trigger = CronTrigger(day=day, hour=hour, minute=minute)
        time_ = f'{day} {hour}:{minute}'

    elif my_types == "year":
        trigger = CronTrigger(month=month, day=day, hour=hour, minute=minute)
        time_ = f'{month} {day} {hour}:{minute}'

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message_id,
        text="🕓 секундочку...",
        parse_mode="HTML"
    )

    await reminder_manager.add_regular_reminder(
        chat_id=chat_id,
        text=txt,
        trigger=trigger,
        small_text=small_text,
        type_="рег.",
        time_next_reminder=time_
    )

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message_id,
        text="✅ <b>Напоминание установлено</b>",
        parse_mode="HTML"
    )
    await state.clear()


########################################################################################################################
""" Интервальные повторения """


class IntervalStt(StatesGroup):
    hour = State()
    minute = State()
    txt = State()
    message_id = State()


@usr_prv.callback_query(StateFilter(None), F.data == "interval")
async def interval(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(IntervalStt.hour)

    await callback.message.edit_text(
        text="Выберите час:",
        reply_markup=inline.choose_hour('interval-h')
    )
    await callback.answer()


@usr_prv.callback_query(IntervalStt.hour, F.data.startswith("interval-h"))
async def interval(callback: types.CallbackQuery, state: FSMContext):
    hour = int(callback.data.split('_')[-1])
    await state.update_data(hour=hour)
    await state.set_state(IntervalStt.minute)

    await callback.message.edit_text(
        text="Выберите минуту:",
        reply_markup=inline.choose_minute('interval-m')
    )
    await callback.answer()


@usr_prv.callback_query(IntervalStt.minute, F.data.startswith("interval-m"))
async def interval_txt(callback: types.CallbackQuery, state: FSMContext):
    minute = int(callback.data.split('_')[-1])
    await state.update_data(minute=minute)
    await state.update_data(message_id=callback.message.message_id)
    await state.set_state(IntervalStt.txt)

    await callback.message.edit_text(
        text="Введите текст для напоминаний"
    )
    await callback.answer()


@usr_prv.message(IntervalStt.txt)
async def interval_save(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Введите текст!")
        return
    await message.delete()

    intervals = [
        timedelta(days=1),
        timedelta(days=3),
        timedelta(days=7),
        timedelta(days=16),
        timedelta(days=35),
        timedelta(days=90),
        timedelta(days=180),
        timedelta(days=365)
    ]

    data = await state.get_data()
    hour = data.get("hour")
    minute = data.get("minute")
    message_id = data.get("message_id")
    chat_id = message.chat.id
    txt = message.text
    small_text = txt if len(txt) < 15 else txt[:15] + '...'
    reminder_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message_id,
        text="🕓 загрузка...",
        parse_mode="HTML"
    )

    async with reminder_manager.scheduler:
        for delta in intervals:
            scheduled_time = reminder_time + delta
            time_ = str(scheduled_time)

            await reminder_manager.add_onetime_reminder(
                chat_id=chat_id,
                text=txt,
                remind_time=reminder_time,
                small_text=small_text,
                type_='инт.',
                time_next_reminder=time_
            )

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message_id,
        text="✅ <b>готово!</b>\n",
        parse_mode="HTML"
    )
    await state.clear()


########################################################################################################################

class ListStt(StatesGroup):
    txt = State()
    reminder_seq = State()


@usr_prv.message(F.text.lower() == "список")
@usr_prv.message(Command('list'))
async def list_reminders(message: types.Message, state: FSMContext):
    await state.clear()
    schedulers = await reminder_manager.scheduler.get_schedules()

    user_reminders = [s for s in schedulers if s.args[0]['chat_id'] == message.chat.id]
    if not user_reminders:
        await message.answer("❌ У вас нет активных напоминаний.")
        return

    status_message = await message.answer(text="🕓 поиск...")

    data = await state.get_data()
    data.get("reminder_seq", list())
    await state.update_data(reminder_seq=user_reminders)

    text = f"<b>ваши активные напоминания:</b>\n"
    for i, reminder in enumerate(user_reminders):
        reminder_data = reminder.args[0]
        txt = reminder_data["small_text"]
        time_ = reminder_data["time_next_reminder"]
        type_ = reminder_data["type_"]
        if txt not in text:
            text += f"{i + 1}) <i>{txt}</i>  -  {time_} ({type_})\n"

    await status_message.edit_text(
        text=text,
        reply_markup=inline.delete_reminder(),
        parse_mode="HTML"
    )


@usr_prv.callback_query(F.data == "remove_remind", StateFilter(None))
async def remove_remind(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(text="введите номер(а) через пробелы")
    await state.set_state(ListStt.txt)


@usr_prv.message(ListStt.txt)
async def remove_r(message: types.Message, state: FSMContext):
    data = await state.get_data()
    reminder_list = data.get('reminder_seq', [])

    try:
        indices = [int(x) - 1 for x in message.text.split()]
    except ValueError:
        await message.answer("❌ Введите корректные номера через пробелы")
        return

    await state.clear()

    deleted = []
    failed = []

    status_message = await message.answer(text="🕓 удаляю...")

    for idx in indices:
        if 0 <= idx < len(reminder_list):
            try:
                reminder = reminder_list[idx]
                job_id = reminder.id
                reminder_data = reminder.args[0]

                # Для интервальных
                if reminder_data.get('type_') == 'инт.':
                    target_text = reminder_data['text']
                    for r in reminder_list:
                        if r.args[0].get('text') == target_text:
                            try:
                                await reminder_manager.scheduler.remove_schedule(r.id)
                                if (idx + 1) not in deleted:
                                    deleted.append(idx + 1)
                            except Exception:
                                failed.append(idx + 1)
                else:
                    try:
                        await reminder_manager.scheduler.remove_schedule(job_id)
                        deleted.append(idx + 1)
                    except Exception:
                        failed.append(idx + 1)
            except Exception:
                failed.append(idx + 1)

    response = []
    if deleted:
        response.append(f"✅ Удалены: {', '.join(map(str, sorted(deleted)))}")
    if failed:
        response.append(f"❌ Не удалось удалить: {', '.join(map(str, sorted(failed)))}")

    await status_message.edit_text("\n".join(response) if response else "❌ Ничего не удалено")
>>>>>>> master
