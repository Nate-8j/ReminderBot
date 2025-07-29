# from aiogram import Bot
# from config import BOT_TOKEN
#
# async def sending_reminder(remind_data):
#     bot = Bot(token=BOT_TOKEN)
#     message_text = (
#         "🔔 Напоминание:\n"
#         "--------------------------------\n"
#         f"«<i>{remind_data['text']}</i>»"
#     )
#     await bot.send_message(chat_id=remind_data['chat_id'], text=message_text, parse_mode="HTML")
#     await bot.session.close()
