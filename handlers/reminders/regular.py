import calendar
from datetime import datetime

from aiogram import types, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from apscheduler.triggers.cron import CronTrigger

from kbds import inline
from handlers.states import RegularStt


class RegularHandlers:
    def __init__(self, bot, reminder_manager, repository):
        self.bot = bot
        self.reminder_manager = reminder_manager
        self.repository = repository
        self.router = Router()

        self.router.callback_query.register(self.regular, StateFilter(None), F.data == "regular")
        self.router.callback_query.register(self.annual_reminders, RegularStt.my_types, F.data == "regular_year")
        self.router.callback_query.register(self.day_of_month, RegularStt.month, F.data.startswith('month_'))
        self.router.callback_query.register(self.monthly_reminders, RegularStt.my_types, F.data == "regular_month")
        self.router.callback_query.register(self.weekly_reminders, RegularStt.my_types, F.data == "regular_week")
        self.router.callback_query.register(self.selected_weekday, RegularStt.weekday, F.data.startswith("week-day"))
        self.router.callback_query.register(self.hours_for_regular, F.data.startswith("day"), RegularStt.day)
        self.router.callback_query.register(self.hours_for_regular, F.data == "farther")
        self.router.callback_query.register(self.hours_for_regular, F.data == "regular_day")
        self.router.callback_query.register(self.minute_for_regula, RegularStt.hour, F.data.startswith("regular-day-h"))
        self.router.callback_query.register(self.txt_for_regular, RegularStt.minute, F.data.startswith("regular-day-m"))
        self.router.message.register(self.saving_regular, RegularStt.txt)

    @staticmethod
    async def regular(callback: types.CallbackQuery, state: FSMContext):
        await state.clear()
        await state.set_state(RegularStt.my_types)
        await callback.message.edit_text(
            "Выберете тип: ",
            reply_markup=inline.type_regular_reminders()
        )
        await callback.answer()

    @staticmethod
    async def annual_reminders(callback: types.CallbackQuery, state: FSMContext):
        await state.update_data(my_types="year")
        await state.set_state(RegularStt.month)
        await callback.message.edit_text(
            text='Выберите месяц:',
            reply_markup=inline.choosing_month()
        )
        await callback.answer()

    @staticmethod
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

    @staticmethod
    async def monthly_reminders(callback: types.CallbackQuery, state: FSMContext):
        await state.update_data(my_types="month")
        await state.set_state(RegularStt.day)
        await callback.message.edit_text(
            text='Выберите день:',
            reply_markup=inline.day_of_month(None)
        )
        await callback.answer()

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    async def minute_for_regula(callback: types.CallbackQuery, state: FSMContext):
        hour = int(callback.data.split('_')[-1])
        await state.update_data(hour=hour)
        await state.set_state(RegularStt.minute)

        await callback.message.edit_text(
            text='Выберите минуту:',
            reply_markup=inline.choose_minute('regular-day-m')
        )
        await callback.answer()

    @staticmethod
    async def txt_for_regular(callback: types.CallbackQuery, state: FSMContext):
        minute = int(callback.data.split('_')[-1])
        await state.update_data(minute=minute)
        await state.update_data(message_id=callback.message.message_id)
        await state.set_state(RegularStt.txt)

        await callback.message.edit_text(
            text="Введите текст напоминания:"
        )
        await callback.answer()

    async def saving_regular(self, message: types.Message, state: FSMContext):
        if not message.text:
            await message.answer("Введите текст!")
            return

        await message.delete()

        data = await state.get_data()

        my_types = data.get('my_types')
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

        await self.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message_id,
            text="🕓 секундочку...",
            parse_mode="HTML"
        )

        job_id = await self.reminder_manager.add_regular_reminder(
            chat_id=message.chat.id,
            text=txt,
            trigger=trigger
        )
        await self.repository.add_reminder(
            job_id=job_id,
            txt=txt,
            small_txt=small_text,
            user_id=message.from_user.id,
            type_='рег.',
            time_next_reminder=time_
        )

        await self.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message_id,
            text="✅ <b>Напоминание установлено</b>",
            parse_mode="HTML"
        )
        await state.clear()

    def get_router(self):
        return self.router
