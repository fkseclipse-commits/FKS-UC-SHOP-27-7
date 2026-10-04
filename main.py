import telebot
from telebot import types
import json
import os
import asyncio
from aiohttp import web
import html
from datetime import datetime, timedelta
import threading

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

ADMIN_CHAT_ID = 8269688160

BALANCE_FILE = "balances.json"
ORDERS_FILE = "orders.json"

def get_uzbekistan_time():
    return datetime.utcnow() + timedelta(hours=5)

def load_balances():
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_balances(data):
    with open(BALANCE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_orders():
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_orders(data):
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

async def api_balance(request):
    user_id = request.query.get('user_id', 'default')
    balances = load_balances()
    user_data = balances.get(str(user_id), {"balance": 0})
    
    if isinstance(user_data, (int, float)):
        balance = user_data
    else:
        balance = user_data.get("balance", 0)
        
    return web.json_response({"balance": balance}, headers={"Access-Control-Allow-Origin": "*"})

async def api_pay(request):
    try:
        data = await request.json()
        user_id = data.get('user_id')
        amount = data.get('amount')
        username = data.get('username', 'Foydalanuvchi')
        payment_method = data.get('payment_method', 'Karta')
        
        if not user_id:
            return web.json_response({"status": "error", "message": "Ma'lumot yetarli emas"}, headers={"Access-Control-Allow-Origin": "*"})
        
        amount_int = int(amount) if amount else 0
        safe_username = html.escape(str(username))
        current_time = get_uzbekistan_time().strftime("%Y-%m-%d %H:%M")
        
        orders = load_orders()
        user_orders = orders.get(str(user_id), [])
        user_orders.append({
            "amount": amount_int,
            "method": payment_method,
            "status": "Kutilmoqda ⏳",
            "date": current_time
        })
        orders[str(user_id)] = user_orders
        save_orders(orders)
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        if amount_int > 0:
            markup.add(
                types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{user_id}_{amount_int}"),
                types.InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{user_id}")
            )
            text = (
                f"💳 <b>Yangi to'lov so'rovi!</b>\n\n"
                f"👤 Foydalanuvchi: {safe_username} (ID: <code>{user_id}</code>)\n"
                f"💰 Summa: <b>{amount_int:,} so'm</b>\n"
                f"📲 Usul: <b>{payment_method}</b>".replace(',', ' ')
            )
        else:
            markup.add(
                types.InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{user_id}")
            )
            text = (
                f"🏛 <b>Bankamat (Naqd) orqali so'rov!</b>\n\n"
                f"👤 Foydalanuvchi: {safe_username} (ID: <code>{user_id}</code>)\n"
                f"📲 Usul: <b>{payment_method}</b>\n"
                f"⚠️ <i>Foydalanuvchi chek yubordi. Iltimos, pul tushganini kartadan tekshiring.</i>"
            )
        
        bot.send_message(ADMIN_CHAT_ID, text, reply_markup=markup, parse_mode="HTML")
        return web.json_response({"status": "success"}, headers={"Access-Control-Allow-Origin": "*"})
    except Exception as e:
        print(f"API_PAY XATOLIGI: {e}")
        return web.json_response({"status": "error", "message": str(e)}, headers={"Access-Control-Allow-Origin": "*"})

async def index(request):
    return web.FileResponse('./index.html')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    balances = load_balances()
    current_time = get_uzbekistan_time().strftime("%Y-%m-%d %H:%M")
    
    if user_id not in balances:
        balances[user_id] = {
            "balance": 0,
            "joined_date": current_time
        }
        save_balances(balances)
    elif isinstance(balances[user_id], (int, float)):
        old_bal = balances[user_id]
        balances[user_id] = {
            "balance": old_bal,
            "joined_date": current_time
        }
        save_balances(balances)
    elif "joined_date" not in balances[user_id]:
        balances[user_id]["joined_date"] = current_time
        save_balances(balances)

    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_profile = types.KeyboardButton("👤 Profil")
    btn_orders = types.KeyboardButton("📦 Buyurtmalarim")
    btn_help = types.KeyboardButton("ℹ️ Yordam")
    
    reply_markup.row(btn_profile)
    reply_markup.row(btn_orders, btn_help)

    markup = types.InlineKeyboardMarkup(row_width=1)
    web_app = types.WebAppInfo(url="https://fks-uc-shop-27-7.vercel.app/")
    markup.add(types.InlineKeyboardButton("🛍 Do'kon", web_app=web_app))

    text = (
        "<b>Xush kelibsiz! 🎉</b>\n\n"
        "💎 <b>FKS UC 27/7 SHOP —</b>\n"
        "PUBG Mobile UC va Telegram Premium xarid qilish xizmati. ⚡💳"
    )
    
    bot.send_message(message.chat.id, "Qo'shimcha funksiyalar uchun pastdagi menyudan foydalaning:", reply_markup=reply_markup)
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    user_id = str(message.from_user.id)
    name = html.escape(message.from_user.first_name)
    username = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
    
    if message.text == "🛍 Do'kon":
        markup = types.InlineKeyboardMarkup()
        web_app = types.WebAppInfo(url="https://fks-uc-shop-27-7.vercel.app/")
        markup.add(types.InlineKeyboardButton("🛍 Do'koni ochish", web_app=web_app))
        bot.send_message(message.chat.id, "Pastdagi tugma orqali do'konga o'ting:", reply_markup=markup)
        
    elif message.text == "👤 Profil":
        balances = load_balances()
        current_time = get_uzbekistan_time().strftime("%Y-%m-%d %H:%M")
        
        if user_id not in balances:
            balances[user_id] = {
                "balance": 0,
                "joined_date": current_time
            }
            save_balances(balances)
            
        user_data = balances.get(user_id)
        
        if isinstance(user_data, (int, float)):
            bal = user_data
            joined = current_time
            balances[user_id] = {"balance": bal, "joined_date": joined}
            save_balances(balances)
        else:
            bal = user_data.get("balance", 0)
            joined = user_data.get("joined_date", current_time)
        
        text = (
            f"👤 <b>Foydalanuvchi Profili</b>\n\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"👤 Ism: {name}\n"
            f"📧 Username: {username}\n"
            f"💰 Balans: <b>{bal:,} UZS</b>".replace(',', ' ') + "\n"
            f"📅 Ro'yxatdan o'tilgan:\n{joined}"
        )
        bot.send_message(message.chat.id, text, parse_mode="HTML")
        
    elif message.text == "📦 Buyurtmalarim":
        orders = load_orders()
        user_orders = orders.get(user_id, [])
        
        if not user_orders:
            text = (
                "🛒 <b>Buyurtmalarim</b>\n\n"
                "❌ Sizda hozircha buyurtmalar mavjud emas.\n\n"
                "🛍 Xarid qilish uchun do'kondan foydalaning!"
            )
        else:
            text = "🛒 <b>Sizning oxirgi buyurtmalaringiz:</b>\n\n"
            for order in user_orders[-5:]:
                text += (
                    f"📦 Summa: <b>{order['amount']:,} so'm</b>\n"
                    f"📲 Usul: {order['method']}\n"
                    f"📌 Holati: {order['status']}\n"
                    f"📅 Sana: {order['date']}\n------------------\n"
                ).replace(',', ' ')
                
        markup = types.InlineKeyboardMarkup()
        web_app = types.WebAppInfo(url="https://fks-uc-shop-27-7.vercel.app/")
        markup.add(types.InlineKeyboardButton("🛍 Do'koni ochish", web_app=web_app))
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")
        
    elif "Yordam" in message.text:
        help_text = (
            "ℹ️ <b>Qo'llanma va Yordam</b>\n\n"
            "Do'kondan foydalanish, balansni to'ldirish va savollar bo'yicha bizning rasmiy kanallarimizga o'ting:\n\n"
            "🔹 <b>UC Server kanal:</b> https://t.me/FKS_UC\n"
            "🔹 <b>Asosiy kanal:</b> https://t.me/FKS_UZ\n\n"
            "💬 <b>Admin bilan bog'lanish:</b> @FKS_PUBGM"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🌐 UC Server Kanal", url="https://t.me/FKS_UC"),
            types.InlineKeyboardButton("📢 Asosiy Kanal", url="https://t.me/FKS_UZ"),
            types.InlineKeyboardButton("💬 Admin bilan bog'lanish", url="https://t.me/FKS_PUBGM")
        )
        
        photo_path = "FKS_PUBGM.jpg" if os.path.exists("FKS_PUBGM.jpg") else "FKS_PUBGM.png"
        
        if os.path.exists(photo_path):
            with open(photo_path, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=help_text, reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, help_text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    data = call.data
    current_time = get_uzbekistan_time().strftime("%Y-%m-%d %H:%M")
    
    if data.startswith("approve_"):
        parts = data.split("_")
        target_user_id = str(parts[1])
        amount = int(parts[2])
        
        balances = load_balances()
        user_data = balances.get(target_user_id, {"balance": 0, "joined_date": current_time})
        
        if isinstance(user_data, (int, float)):
            current_bal = user_data
            joined = current_time
        else:
            current_bal = user_data.get("balance", 0)
            joined = user_data.get("joined_date", current_time)
            
        new_bal = current_bal + amount
        
        balances[target_user_id] = {
            "balance": new_bal,
            "joined_date": joined
        }
        save_balances(balances)
        
        orders = load_orders()
        if target_user_id in orders and orders[target_user_id]:
            orders[target_user_id][-1]["status"] = "✅ Tasdiqlandi (Bajarildi)"
            save_orders(orders)
        
        try:
            bot.send_message(
                target_user_id, 
                f"✅ Tabriklaymiz! To'lovingiz tasdiqlandi va balansingizga {amount:,} so'm qo'shildi! 🎉\n💰 Yangi balans: {new_bal:,} so'm".replace(',', ' ')
            )
        except Exception as e:
            print("Xatolik:", e)
            
        bot.answer_callback_query(call.id, "Muvaffaqiyatli tasdiqlandi va balansga qo'shildi!")
        bot.edit_message_text(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            text=call.message.text + f"\n\n✅ HOLAT: Tasdiqlandi ({amount:,} so'm qo'shildi)".replace(',', ' ')
        )

    elif data.startswith("reject_"):
        parts = data.split("_")
        target_user_id = str(parts[1])
        
        orders = load_orders()
        if target_user_id in orders and orders[target_user_id]:
            orders[target_user_id][-1]["status"] = "❌ Rad etildi"
            save_orders(orders)
        
        try:
            bot.send_message(
                target_user_id, 
                "❌ Afsuski, sizning to'lovingiz bekor qilindi (rad etildi)."
            )
        except Exception as e:
            print("Xatolik:", e)
            
        bot.answer_callback_query(call.id, "To'lov rad etildi.")
        bot.edit_message_text(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            text=call.message.text + f"\n\n❌ HOLAT: Rad etildi / Bekor qilindi."
        )

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', index)
    app.router.add_get('/index.html', index)
    app.router.add_get('/api/balance', api_balance)
    app.router.add_post('/api/pay', api_pay)
    app.router.add_static('/static/', path='./', name='static')

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

def run_bot():
    try:
        bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        print("Webhookni o'chirishda xatolik:", e)
        
    while True:
        try:
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            print(f"Polling xatosi: {e}")
            import time
            time.sleep(5)

async def main():
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    await start_web_server()
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
 
 

 
