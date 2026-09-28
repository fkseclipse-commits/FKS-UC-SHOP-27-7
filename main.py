import telebot
from telebot import types
import json
import os

TOKEN = "8965938163:AAE5-fezkpV-zUI_Ti4k5JRavmw6pWRjN78"
bot = telebot.TeleBot(TOKEN)

# Balanslarni saqlab turish uchun fayl nomi
BALANCE_FILE = "balances.json"

# Fayldan balanslarni o'qib olish
def load_balances():
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

# Balanslarni faylga saqlash
def save_balances(data):
    with open(BALANCE_FILE, "w") as f:
        json.dump(data, f)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    balances = load_balances()
    
    # Agar foydalanuvchi birinchi marta kelsa, balansini 0 qilish
    if user_id not in balances:
        balances[user_id] = 0
        save_balances(balances)

    markup = types.InlineKeyboardMarkup()
    web_app = types.WebAppInfo(url="https://fks-uc-shop-27-7.vercel.app")
    markup.add(types.InlineKeyboardButton("🎮 Do'konga kirish", web_app=web_app))
    
    bot.reply_to(message, "Assalomu alaykum! FKS PUBGM SHOP botiga xush kelibsiz. Quyidagi tugma orqali do'konga o'ting:", reply_markup=markup)

# Balansni tekshirish uchun maxsus buyruq (agar kerak bo'lsa)
@bot.message_handler(commands=['balance'])
def check_balance(message):
    user_id = str(message.from_user.id)
    balances = load_balances()
    current_bal = balances.get(user_id, 0)
    bot.reply_to(message, f"Sizning balansingiz: {current_bal:,} so'm".replace(',', ' '))

# Admin tugmani bosganda ishlaydigan qism
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    data = call.data
    
    if data.startswith("approve_"):
        parts = data.split("_")
        user_id = parts[1]
        amount = int(parts[2])
        
        # Bazadan foydalanuvchi balansini o'qib, unga pulni qo'shish
        balances = load_balances()
        current_bal = balances.get(user_id, 0)
        new_bal = current_bal + amount
        balances[user_id] = new_bal
        save_balances(balances)
        
        # Foydalanuvchiga xabar yuborish
        try:
            bot.send_message(user_id, f"✅ Tabriklaymiz! To'lovingiz tasdiqlandi va balansingizga {amount:,} so'm qo'shildi! 🎉\n💰 Yangi balans: {new_bal:,} so'm".replace(',', ' '))
        except Exception as e:
            print("Foydalanuvchiga yozib bo'lmadi:", e)
            
        bot.answer_callback_query(call.id, "To'lov muvaffaqiyatli tasdiqlandi va balansga qo'shildi!")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text + f"\n\n✅ HOLAT: Tasdiqlandi ({amount:,} so'm qo'shildi)".replace(',', ' '))
        
    elif data.startswith("reject_"):
        parts = data.split("_")
        user_id = parts[1]
        
        try:
            bot.send_message(user_id, "❌ Afsuski, to'lovingiz rad etildi yoki admin tomonidan bekor qilindi.")
        except Exception as e:
            print("Foydalanuvchiga yozib bo'lmadi:", e)
            
        bot.answer_callback_query(call.id, "To'lov rad etildi.")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text + "\n\n❌ HOLAT: Rad etildi.")

if __name__ == "__main__":
    print("Bot ishga tushdi...")
    bot.infinity_polling()
 
