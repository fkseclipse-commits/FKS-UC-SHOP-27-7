import telebot
from telebot import types
import json
import os
import asyncio
from aiohttp import web
import html
from datetime import datetime

TOKEN = "8965938163:AAE5-fezkpV-zUI_Ti4k5JRavmw6pWRjN78"
bot = telebot.TeleBot(TOKEN)

ADMIN_CHAT_ID = 8269688160

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

# Veb-sayt balansni olishi uchun API
async def api_balance(request):
    user_id = request.query.get('user_id', 'default')
    balances = load_balances()
    balance = balances.get(str(user_id), 0)
    return web.json_response({"balance": balance}, headers={"Access-Control-Allow-Origin": "*"})

# Saytdan to'lov so'rovi kelganda botga xabar yuborish
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
    
    if user_id not in balances:
        balances[user_id] = 0
        save_balances(balances)

    # Pastdagi Reply menyu
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
        "PUBG Mobile UC va Telegram Premium xarid qilish xizmati. ⚡️💳"
    )
    
    bot.send_message(message.chat.id, "Qo'shimcha funksiyalar uchun pastdagi menyudan foydalaning:", reply_markup=reply_markup)
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")

# Pastdagi menyu tugmalari bosilganda ishlaydigan qism
@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    user_id = str(message.from_user.id)
    name = html.escape(message.from_user.first_name)
    username = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    if message.text == "🛍 Do'kon":
        markup = types.InlineKeyboardMarkup()
        web_app = types.WebAppInfo(url="https://fks-uc-shop-27-7.vercel.app/")
        markup.add(types.InlineKeyboardButton("🛍 Do'koni ochish", web_app=web_app))
        bot.send_message(message.chat.id, "Pastdagi tugma orqali do'konga o'ting:", reply_markup=markup)
        
    elif message.text == "👤 Profil":
        balances = load_balances()
        bal = balances.get(user_id, 0)
        
        text = (
            f"👤 <b>Foydalanuvchi Profili</b>\n\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"👤 Ism: {name}\n"
            f"📧 Username: {username}\n"
            f"💰 Balans: <b>{bal:,} UZS</b>".replace(',', ' ') + "\n"
            f"📅 Ro'yxatdan o'tilgan:\n{current_time}"
        )
        bot.send_message(message.chat.id, text, parse_mode="HTML")
        
    elif message.text == "📦 Buyurtmalarim":
        text = (
            f"🛒 <b>Oxirgi buyurtmangiz:</b>\n\n"
            f"💎 <b>60 UC</b>\n"
            f"Holati: ✅ <b>Bajarildi</b>\n"
            f"Summa: 12,000 UZS\n"
            f"Sana: {current_time}"
        )
        bot.send_message(message.chat.id, text, parse_mode="HTML")
        
    elif message.text == "ℹ️ Yordam":
        help_text = (
            "ℹ️ <b>Qo'llanma va Yordam</b>\n\n"
            "Do'kondan foydalanish va balansni to'ldirish bo'yicha savollar uchun admin bilan bog'laning:\n\n"
            "💬 <b>Admin:</b> @FKS_PUBGM"
        )
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("💬 Murojaat qilish", url="https://t.me/FKS_PUBGM")
        )
        
        photo_path = "20028.png"  # Siz yuborgan rasm fayl nomi
        if os.path.exists(photo_path):
            with open(photo_path, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=help_text, reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, help_text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    data = call.data
    user_id = str(call.from_user.id)
    
    if data.startswith("approve_"):
        parts = data.split("_")
        target_user_id = str(parts[1])
        amount = int(parts[2])
        
        balances = load_balances()
        current_bal = balances.get(target_user_id, 0)
        new_bal = current_bal + amount
        balances[target_user_id] = new_bal
        save_balances(balances)
        
        try:
            bot.send_message(target_user_id, f"✅ Tabriklaymiz! To'lovingiz tasdiqlandi va balansingizga {amount:,} so'm qo'shildi! 🎉\n💰 Yangi balans: {new_bal:,} so'm".replace(',', ' '))
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
        
        try:
            bot.send_message(target_user_id, "❌ Afsuski, to'lovingiz rad etildi.")
        except Exception as e:
            print("Xatolik:", e)
            
        bot.answer_callback_query(call.id, "To'lov rad etildi.")
        bot.edit_message_text(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            text=call.message.text + "\n\n❌ HOLAT: Rad etildi."
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

async def main():
    asyncio.create_task(start_web_server())
    while True:
        try:
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
 
 

 
