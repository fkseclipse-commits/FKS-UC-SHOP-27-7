import telebot
from telebot import types
import json
import os

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

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    balances = load_balances()
    
    if user_id not in balances:
        balances[user_id] = 0
        save_balances(balances)

    markup = types.InlineKeyboardMarkup()
    web_app = types.WebAppInfo(url="https://fks-uc-shop-27-7.vercel.app")
    markup.add(types.InlineKeyboardButton("🎮 Do'konga kirish", web_app=web_app))
    
    bot.reply_to(message, "Assalomu alaykum! FKS PUBGM SHOP botiga xush kelibsiz. Do'konga kirish uchun pastdagi tugmani bosing:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    data = call.data
    
    try:
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
                bot.send_message(user_id, f"✅ Tabriklaymiz! To'lovingiz tasdiqlandi va balansingizga {amount:,} so'm qo'shildi! 🎉".replace(',', ' '))
            except Exception as e:
                print("Foydalanuvchiga yozib bo'lmadi:", e)
                
            bot.answer_callback_query(call.id, "Muvaffaqiyatli tasdiqlandi!")
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
    except Exception as err:
        print("Xatolik yuz berdi:", err)
        bot.answer_callback_query(call.id, "Xatolik yuz berdi!")

if __name__ == "__main__":
    print("Bot ishga tushdi...")
    bot.infinity_polling()
 
