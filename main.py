import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '8965938163:AAE5-fezkpV-zUI_Ti4k5JRavmw6pWRjN78'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Foydalanuvchilar balansini saqlab turuvchi baza (lug'at)
user_balances = {}

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    web_app = WebAppInfo(url="https://fks-uc-shop-27-7.vercel.app/")

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

@dp.callback_query_handler(lambda call: True)
async def callback_handler(call: types.CallbackQuery):
    data = call.data
    
    if data.startswith("approve_"):
        parts = data.split("_")
        user_id = int(parts[1])
        amount = int(parts[2])
        
        # Balansga pulni qo'shish
        if user_id not in user_balances:
            user_balances[user_id] = 0
        user_balances[user_id] += amount
        
        # Adminga xabar berish
        await bot.answer_callback_query(call.id, f"✅ Muvaffaqiyatli! Foydalanuvchiga {amount} so'm qo'shildi.")
        
        # Xabarni yangilash
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=call.message.text + f"\n\n✅ <b>HOLAT:</b> Tasdiqlandi ({amount} so'm qo'shildi)",
            parse_mode="HTML"
        )
        
        # Foydalanuvchiga xabar yuborish
        try:
            await bot.send_message(user_id, f"🎉 Tabriklaymiz! Hisobingiz {amount} so'mga to'ldirildi. Hozirgi balans: {user_balances[user_id]} so'm.")
        except:
            pass

    elif data.startswith("reject_"):
        parts = data.split("_")
        user_id = int(parts[1])
        
        await bot.answer_callback_query(call.id, "❌ To'lov rad etildi!")
        
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=call.message.text + "\n\n❌ <b>HOLAT:</b> Bekor qilindi",
            parse_mode="HTML"
        )
        
        try:
            await bot.send_message(user_id, "❌ Afsuski, to'lov so'rovingiz rad etildi.")
        except:
            pass

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
 
 
