import telebot
from telebot import types

TOKEN = "8965938163:AAE5-fezkpV-zUI_Ti4k5JRavmw6pWRjN78"
bot = telebot.TeleBot(TOKEN)

# Foydalanuvchilar balansini vaqtinchalik xotirada saqlash uchun
user_balances = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    # Mini App ochish tugmasi
    web_app = types.WebAppInfo(url="https://fks-uc-shop-27-7.vercel.app")
    markup.add(types.InlineKeyboardButton("🎮 Do'konga kirish", web_app=web_app))
    
    bot.reply_to(message, "Assalomu alaykum! FKS PUBGM SHOP botiga xush kelibsiz. Quyidagi tugma orqali do'konga o'ting:", reply_markup=markup)

# Admin tugmani bosganda ishlaydigan qism (Callback query)
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    data = call.data
    
    if data.startswith("approve_"):
        parts = data.split("_")
        user_id = parts[1]
        amount = int(parts[2])
        
        # Bu yerda foydalanuvchiga xabar yuboriladi
        try:
            bot.send_message(user_id, f"✅ Tabriklaymiz! To'lovingiz tasdiqlandi va balansingizga {amount:,} so'm qo'shildi! 🎉".replace(',', ' '))
        except Exception as e:
            print("Foydalanuvchiga yozib bo'lmadi:", e)
            
        bot.answer_callback_query(call.id, "To'lov muvaffaqiyatli tasdiqlandi!")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text + "\n\n✅ HOLAT: Tasdiqlandi va yakunlandi.")
        
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
 
 
 
 
