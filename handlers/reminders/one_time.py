from datetime import datetime

from aiogram import types, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from kbds import inline
from handlers.states import OneTimeStt

from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback


class OneTimeHandlers:
    def __init__(self, bot, reminder_manager, repository):
        self.bot = bot
        self.reminder_manager = reminder_manager
        self.repository = repository
        self.router = Router()

        self.router.callback_query.register(self.onetime_nav_cal_handler, StateFilter(None), F.data == "one")
        self.router.callback_query.register(self.onetime_calendar, SimpleCalendarCallback.filter(), OneTimeStt.date)
        self.router.callback_query.register(self.onetime_hour, F.data.startswith('one-h'), OneTimeStt.hour)
        self.router.callback_query.register(self.onetime_minute, F.data.startswith('one-m'), OneTimeStt.minute)
        self.router.message.register(self.onetime_txt, OneTimeStt.txt)

    @staticmethod
    async def onetime_nav_cal_handler(callback: types.CallbackQuery, state: FSMContext):
        await callback.message.edit_text(
            "Пожалуйста выберите дату: ",
            reply_markup=await SimpleCalendar().start_calendar()  # locale='ru_RU.UTF-8'
        )
        await state.set_state(OneTimeStt.date)

    @staticmethod
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
            await state.set_state(OneTimeStt.hour)
            await callback_query.message.edit_text(
                "Выберите час: ",
                reply_markup=inline.choose_hour('one-h')
            )

            await callback_query.answer()

    @staticmethod
    async def onetime_hour(callback: types.CallbackQuery, state: FSMContext):
        hour = int(callback.data.split('_')[-1])
        await state.update_data(hour=hour)
        await state.set_state(OneTimeStt.minute)
        await callback.message.edit_text(
            "Выберите минуты: ",
            reply_markup=inline.choose_minute('one-m')
        )
        await callback.answer()

    @staticmethod
    async def onetime_minute(callback: CallbackQuery, state: FSMContext):
        minute = int(callback.data.split('_')[-1])
        await state.update_data(
            minute=minute,
            message_id=callback.message.message_id
        )
        await state.set_state(OneTimeStt.txt)
        await callback.message.edit_text(
            f"Введите текст напоминания"
        )
        await callback.answer()

    async def onetime_txt(self, message: types.Message, state: FSMContext):
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

        await self.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=data['message_id'],
            text="🕓 добавляю...",
            parse_mode="HTML"
        )

        job_id = await self.reminder_manager.add_onetime_reminder(
            chat_id=message.chat.id,
            text=txt,
            remind_time=remind_date,
        )
        await self.repository.add_reminder(
            job_id=job_id,
            txt=txt,
            small_txt=small_text,
            user_id=message.from_user.id,
            type_='раз.',
            time_next_reminder=time_
        )

        formatted_text = (
            f"✅ <b>Напоминание установлено</b>\n"
            f"📅 <i>{remind_date.strftime('%d.%m.%Y %H:%M')}</i>"
        )

        await self.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=data['message_id'],
            text=formatted_text,
            parse_mode="HTML"
        )
        await state.clear()

    def get_router(self):
        return self.router