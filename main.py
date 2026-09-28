import telebot
from telebot import types
import json
import os
from aiohttp import web

TOKEN = "8965938163:AAE5-fezkpV-zUI_Ti4k5JRavmw6pWRjN78"
bot = telebot.TeleBot(TOKEN)

BALANCE_FILE = "balances.json"

def load_balances():
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_balances(data):
    with open(BALANCE_FILE, "w") as f:
        json.dump(data, f)

# Veb-sayt balansni tekshirishi uchun API qismi
async def api_balance(request):
    user_id = request.query.get('user_id', 'default')
    balances = load_balances()
    balance = balances.get(str(user_id), 0)
    return web.json_response({"balance": balance})

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    balances = load_balances()
    
    if user_id not in balances:
        balances[user_id] = 0
        save_balances(balances)

    web_app = types.WebAppInfo(url="https://fks-uc-shop-27-7.vercel.app")

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🛍 Do'kon", web_app=web_app),
        types.InlineKeyboardButton("👤 Profil", callback_data="profile"),
        types.InlineKeyboardButton("📜 Buyurtmalarim", callback_data="orders"),
        types.InlineKeyboardButton("ℹ️ Yordam", callback_data="help")
    )

    text = (
        "<b>Xush kelibsiz, 🎉!</b>\n\n"
        "💎 <b>UC2407 DONAT SHOP —</b>\n"
        "PUBG Mobile UC va boshqa o'yin valyutalarini tezkor va qulay xarid qilish xizmati. ⚡️💳"
    )
    bot.reply_to(message, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    data = call.data
    
    if data.startswith("approve_"):
        parts = data.split("_")
        user_id = str(parts[1])
        amount = int(parts[2])
        
        balances = load_balances()
        current_bal = balances.get(user_id, 0)
        new_bal = current_bal + amount
        balances[user_id] = new_bal
        save_balances(balances)
        
        try:
            bot.send_message(user_id, f"✅ Tabriklaymiz! To'lovingiz tasdiqlandi va balansingizga {amount:,} so'm qo'shildi! 🎉\n💰 Yangi balans: {new_bal:,} so'm".replace(',', ' '))
        except Exception as e:
            print("Foydalanuvchiga yozib bo'lmadi:", e)
            
        bot.answer_callback_query(call.id, "Muvaffaqiyatli tasdiqlandi va balansga qo'shildi!")
        bot.edit_message_text(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            text=call.message.text + f"\n\n✅ HOLAT: Tasdiqlandi ({amount:,} so'm qo'shildi)".replace(',', ' ')
        )
        
    elif data.startswith("reject_"):
        parts = data.split("_")
        user_id = str(parts[1])
        
        try:
            bot.send_message(user_id, "❌ Afsuski, to'lovingiz rad etildi.")
        except Exception as e:
            print("Foydalanuvchiga yozib bo'lmadi:", e)
            
        bot.answer_callback_query(call.id, "To'lov rad etildi.")
        bot.edit_message_text(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            text=call.message.text + "\n\n❌ HOLAT: Rad etildi."
        )
        
    elif data == "profile":
        user_id = str(call.from_user.id)
        balances = load_balances()
        bal = balances.get(user_id, 0)
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"👤 <b>Sizning profilingiz:</b>\n\n🆔 ID: <code>{user_id}</code>\n💰 Balans: {bal:,} so'm".replace(',', ' '), parse_mode="HTML")

    elif data == "orders":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📜 Xaridlar tarixingizni ko'rish uchun saytdagi 'Tarix' bo'limiga o'ting.")

    elif data == "help":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "ℹ️ Yordam uchun admin bilan bog'laning: @Jv_asilbek")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/api/balance', api_balance)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

if __name__ == "__main__":
    import asyncio
    import threading
    
    # API serverni fonda ishga tushirish
    loop = asyncio.get_event_loop()
    loop.create_task(start_web_server())
    
    print("Bot va API server ishga tushdi...")
    bot.infinity_polling()
 
 
