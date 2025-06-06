from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


add_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="добавить"),
            KeyboardButton(text="список")
        ],
    ],
    resize_keyboard=True
)