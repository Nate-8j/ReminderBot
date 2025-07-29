from aiogram import types, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from kbds import inline
from handlers.states import ListStt


class ListHandlers:
    def __init__(self, reminder_manager, repository):
        self.reminder_manager = reminder_manager
        self.repository = repository
        self.router = Router()

        self.router.message.register(self.list_reminders, F.text.lower() == "список")
        self.router.message.register(self.list_reminders, Command('list'))
        self.router.message.register(self.remove_remind, F.data == "remove_remind", StateFilter(None))
        self.router.message.register(self.remove_r, ListStt.txt)

    async def list_reminders(self, message: types.Message, state: FSMContext):
        await state.clear()

        schedulers = await self.repository.get_reminders(message.from_user.id)
        user_reminders = [s for s in schedulers if s['time_next_reminder'] is not None]

        if not user_reminders:
            await message.answer("❌ У вас нет активных напоминаний.")
            return

        status_message = await message.answer(text="🕓 поиск...")

        data = await state.get_data()
        data.get("reminder_seq", list())
        await state.update_data(reminder_seq=user_reminders)

        text = f"<b>ваши активные напоминания:</b>\n"
        for i, reminder in enumerate(user_reminders, start=1):
            txt = reminder["small_txt"]
            time_ = reminder["time_next_reminder"]
            type_ = reminder["type_"]
            text += f"{i}) <i>{txt}</i>  -  {time_} ({type_})\n"

        await status_message.edit_text(
            text=text,
            reply_markup=inline.delete_reminder(),
            parse_mode="HTML"
        )

    @staticmethod
    async def remove_remind(callback: types.CallbackQuery, state: FSMContext):
        await callback.message.answer(text="введите номер(а) через пробелы")
        await state.set_state(ListStt.txt)

    async def remove_r(self, message: types.Message, state: FSMContext):
        data = await state.get_data()
        reminder_list = data.get('reminder_seq', [])

        try:
            indices = [int(x) - 1 for x in message.text.split()]
        except ValueError:
            await message.answer("❌ Введите корректные номера через пробелы")
            return
        await state.clear()

        status_message = await message.answer(text="🕓 удаляю...")

        deleted = []
        for idx in indices:
            if 0 < idx < len(reminder_list):
                try:
                    reminder = reminder_list[idx - 1]
                    job_id = reminder['job_id']

                    await self.reminder_manager.scheduler.remove_schedule(job_id)
                    deleted.append(str(idx))
                except Exception:
                    pass

        await status_message.edit_text(text=f"✅ Удалены: {', '.join(deleted)}" if deleted else "❌ Ошибка")

    def get_router(self):
        return self.router