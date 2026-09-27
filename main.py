import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

API_TOKEN = '8965938163:AAE5-fezkpV-zUI_Ti4k5JRavmw6pWRjN78'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Foydalanuvchilar balansi va tarixi saqlanadigan joy
user_balances = {}
user_history = {}
all_purchases = []

# --- VEB-SAYT UCHUN API QISMI ---
async def api_balance(request):
    user_id = request.query.get('user_id', 'default')
    try:
        uid = int(user_id)
    except:
        uid = user_id
    balance = user_balances.get(uid, 0)
    return web.json_response({"balance": balance})

async def api_history(request):
    user_id = request.query.get('user_id', 'default')
    try:
        uid = int(user_id)
    except:
        uid = user_id
    history = user_history.get(uid, [])
    return web.json_response(history)

async def api_top_buyers(request):
    buyers_map = {}
    for p in all_purchases:
        name = p.get('username', 'Foydalanuvchi')
        price = p.get('price', 0)
        buyers_map[name] = buyers_map.get(name, 0) + price
    result = [{"name": name, "total": total} for name, total in buyers_map.items()]
    return web.json_response(result)

async def api_buy(request):
    data = await request.json()
    user_id = data.get('user_id')
    try:
        uid = int(user_id)
    except:
        uid = user_id
    
    item_name = data.get('item_name')
    price = data.get('price', 0)
    username = data.get('username', 'Foydalanuvchi')
    extra_info = data.get('extra_info', '')

    current_balance = user_balances.get(uid, 0)
    if current_balance < price:
        return web.json_response({"success": False, "message": "Balansda mablag' yetarli emas!"})

    user_balances[uid] = current_balance - price
    
    if uid not in user_history:
        user_history[uid] = []
    
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    user_history[uid].insert(0, {
        "item_name": item_name,
        "price": price,
        "extra_info": extra_info,
        "date": date_str
    })
    
    all_purchases.append({"username": username, "price": price})

    return web.json_response({"success": True, "new_balance": user_balances[uid]})


# --- TELEGRAM BOT QISMI ---
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
        
        if user_id not in user_balances:
            user_balances[user_id] = 0
        user_balances[user_id] += amount
        
        await bot.answer_callback_query(call.id, f"✅ Muvaffaqiyatli! Foydalanuvchiga {amount} so'm qo'shildi.")
        
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=call.message.text + f"\n\n✅ <b>HOLAT:</b> Tasdiqlandi ({amount} so'm qo'shildi)",
            parse_mode="HTML"
        )
        
        try:
            await bot.send_message(user_id, f"🎉 Tabriklaymiz! Hisobingiz {amount} so'mga to'ldirildi. Yangi balans: {user_balances[user_id]} so'm.")
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


# Serverni bot bilan birga ishga tushirish
async def on_startup(dispatcher):
    app = web.Application()
    app.router.add_get('/api/balance', api_balance)
    app.router.add_get('/api/history', api_history)
    app.router.add_get('/api/top-buyers', api_top_buyers)
    app.router.add_post('/api/buy', api_buy)
    
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"API Server started on port {port}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
 
 
 
