import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '8965938163:AAE5-fezkpV-zUI_Ti4k5JRavmw6pWRjN78'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    web_app = WebAppInfo(url="https://sizning-webapp-saytingiz.uz")
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(text="🛍 Do'kon", web_app=web_app),
        InlineKeyboardButton(text="👤 Profil", callback_data="profile"),
        InlineKeyboardButton(text="📦 Buyurtmalarim", callback_data="orders"),
        InlineKeyboardButton(text="ℹ️ Yordam", callback_data="help")
    )
    
    text = (
        "<b>Xush kelibsiz, 🎉!</b>\n\n"
        "💎 <b>UC2407 DONAT SHOP —</b>\n"
        "PUBG Mobile UC va boshqa o'yin valyutalarini tezkor va qulay xarid qilish xizmati. ⚡️💳"
    )
    await message.answer(text, reply_markup=markup, parse_mode="HTML")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
