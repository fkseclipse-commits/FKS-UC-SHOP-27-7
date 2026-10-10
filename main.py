import os
import asyncio
import html
import threading
from datetime import datetime, timedelta

import telebot
from telebot import types
from aiohttp import web
import psycopg
from psycopg.rows import dict_row

# Railway Variables:
# BOT_TOKEN = your Telegram bot token
# DATABASE_URL = Railway PostgreSQL connection URL
TOKEN = os.environ.get("BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
ADMIN_CHAT_ID = 8269688160

if not TOKEN:
    raise RuntimeError("BOT_TOKEN Railway Variables ichida sozlanmagan.")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL Railway Variables ichida sozlanmagan.")

bot = telebot.TeleBot(TOKEN)


def get_uzbekistan_time():
    return datetime.utcnow() + timedelta(hours=5)


def db_connect():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db():
    with db_connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                balance BIGINT NOT NULL DEFAULT 0,
                joined_date TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                user_id BIGINT NOT NULL,
                amount BIGINT NOT NULL CHECK (amount > 0),
                method TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Kutilmoqda ⏳',
                created_at TEXT NOT NULL,
                processed_at TEXT
            )
        """)


def ensure_user(user_id):
    user_id = int(user_id)
    now = get_uzbekistan_time().strftime("%Y-%m-%d %H:%M")
    with db_connect() as conn:
        conn.execute("""
            INSERT INTO users (user_id, balance, joined_date)
            VALUES (%s, 0, %s)
            ON CONFLICT (user_id) DO NOTHING
        """, (user_id, now))


def get_balance(user_id):
    ensure_user(user_id)
    with db_connect() as conn:
        row = conn.execute(
            "SELECT balance FROM users WHERE user_id = %s",
            (int(user_id),)
        ).fetchone()
        return int(row["balance"]) if row else 0


async def api_balance(request):
    user_id = request.query.get("user_id", "")
    try:
        if not user_id.isdigit():
            raise ValueError("invalid user")
        balance = get_balance(user_id)
        return web.json_response(
            {"balance": balance},
            headers={"Access-Control-Allow-Origin": "*"}
        )
    except Exception as e:
        print(f"API_BALANCE XATOLIGI: {e}")
        return web.json_response(
            {"status": "error", "message": "Balansni olib bo'lmadi"},
            status=400,
            headers={"Access-Control-Allow-Origin": "*"}
        )


async def api_pay(request):
    try:
        data = await request.json()
        raw_user_id = str(data.get("user_id", ""))
        username = str(data.get("username", "Foydalanuvchi"))
        method = str(data.get("payment_method", "Uzcard/Humo"))[:80]

        try:
            amount = int(data.get("amount", 0))
        except (TypeError, ValueError):
            amount = 0

        if not raw_user_id.isdigit() or amount <= 0:
            return web.json_response(
                {"status": "error", "message": "Foydalanuvchi yoki summa noto'g'ri"},
                status=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        import uuid
        order_id = uuid.uuid4().hex[:12]
        now = get_uzbekistan_time().strftime("%Y-%m-%d %H:%M")

        with db_connect() as conn:
            conn.execute("""
                INSERT INTO users (user_id, balance, joined_date)
                VALUES (%s, 0, %s)
                ON CONFLICT (user_id) DO NOTHING
            """, (int(raw_user_id), now))
            conn.execute("""
                INSERT INTO orders (order_id, user_id, amount, method, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (order_id, int(raw_user_id), amount, method, "Kutilmoqda ⏳", now))

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton(
                "✅ Tasdiqlash",
                callback_data=f"approve_{raw_user_id}_{order_id}"
            ),
            types.InlineKeyboardButton(
                "❌ Bekor qilish",
                callback_data=f"reject_{raw_user_id}_{order_id}"
            )
        )

        safe_username = html.escape(username)
        safe_method = html.escape(method)
        text = (
            "💳 <b>Yangi balans to'ldirish so'rovi!</b>\n\n"
            f"👤 Mijoz: {safe_username}\n"
            f"🆔 ID: <code>{raw_user_id}</code>\n"
            f"💰 Summa: <b>{amount:,} so'm</b>\n"
            f"📲 Usul: <b>{safe_method}</b>\n"
            f"🧾 Buyurtma: <code>{order_id}</code>\n\n"
            "⚠️ Pul kartaga haqiqatan tushganini tekshiring."
        ).replace(",", " ")

        try:
            bot.send_message(ADMIN_CHAT_ID, text, reply_markup=markup, parse_mode="HTML")
        except Exception as e:
            print(f"Adminga xabar yuborilmadi: {e}")
            # Don't leave an unnotified request pending.
            with db_connect() as conn:
                conn.execute(
                    "UPDATE orders SET status = %s WHERE order_id = %s AND status = %s",
                    ("Xabar yuborilmadi — tekshirish kerak", order_id, "Kutilmoqda ⏳")
                )
            return web.json_response(
                {"status": "error", "message": "Adminga xabar yuborilmadi. Qayta urinib ko'ring."},
                status=500,
                headers={"Access-Control-Allow-Origin": "*"}
            )

        return web.json_response(
            {"status": "success", "order_id": order_id},
            headers={"Access-Control-Allow-Origin": "*"}
        )
    except Exception as e:
        print(f"API_PAY XATOLIGI: {e}")
        return web.json_response(
            {"status": "error", "message": "To'lov so'rovini yuborib bo'lmadi"},
            status=500,
            headers={"Access-Control-Allow-Origin": "*"}
        )


async def index(request):
    return web.FileResponse("./index.html")


@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = message.from_user.id
    ensure_user(user_id)

    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    reply_markup.row(types.KeyboardButton("👤 Profil"))
    reply_markup.row(
        types.KeyboardButton("📦 Buyurtmalarim"),
        types.KeyboardButton("ℹ️ Yordam")
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    web_app = types.WebAppInfo(url="https://fks-uc-shop-27-7.vercel.app/")
    markup.add(types.InlineKeyboardButton("🛍 Do'kon", web_app=web_app))

    text = (
        "<b>Xush kelibsiz! 🎉</b>\n\n"
        "💎 <b>FKS UC 27/7 SHOP</b>\n"
        "PUBG Mobile UC va Telegram Premium xarid qilish xizmati. ⚡💳"
    )
    bot.send_message(
        message.chat.id,
        "Qo'shimcha funksiyalar uchun pastdagi menyudan foydalaning:",
        reply_markup=reply_markup
    )
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")


@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    user_id = message.from_user.id
    name = html.escape(message.from_user.first_name or "Foydalanuvchi")
    username = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"

    if message.text == "👤 Profil":
        ensure_user(user_id)
        with db_connect() as conn:
            user = conn.execute(
                "SELECT balance, joined_date FROM users WHERE user_id = %s",
                (user_id,)
            ).fetchone()
        bot.send_message(
            message.chat.id,
            (
                "👤 <b>Foydalanuvchi profili</b>\n\n"
                f"🆔 ID: <code>{user_id}</code>\n"
                f"👤 Ism: {name}\n"
                f"📧 Username: {html.escape(username)}\n"
                f"💰 Balans: <b>{user['balance']:,} UZS</b>\n"
                f"📅 Ro'yxatdan o'tilgan: {user['joined_date']}"
            ).replace(",", " "),
            parse_mode="HTML"
        )

    elif message.text == "📦 Buyurtmalarim":
        with db_connect() as conn:
            rows = conn.execute("""
                SELECT amount, method, status, created_at
                FROM orders WHERE user_id = %s
                ORDER BY created_at DESC LIMIT 5
            """, (user_id,)).fetchall()

        if not rows:
            text = (
                "🛒 <b>Buyurtmalarim</b>\n\n"
                "❌ Hozircha buyurtmalaringiz yo'q."
            )
        else:
            text = "🛒 <b>Oxirgi buyurtmalaringiz:</b>\n\n"
            for order in rows:
                text += (
                    f"💰 Summa: <b>{order['amount']:,} so'm</b>\n"
                    f"📲 Usul: {html.escape(order['method'])}\n"
                    f"📌 Holati: {html.escape(order['status'])}\n"
                    f"📅 Sana: {html.escape(order['created_at'])}\n"
                    "------------------\n"
                )
            text = text.replace(",", " ")

        markup = types.InlineKeyboardMarkup()
        web_app = types.WebAppInfo(url="https://fks-uc-shop-27-7.vercel.app/")
        markup.add(types.InlineKeyboardButton("🛍 Do'konni ochish", web_app=web_app))
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")

    elif message.text and "Yordam" in message.text:
        help_text = (
            "ℹ️ <b>Qo'llanma va yordam</b>\n\n"
            "🔹 UC Server kanal: https://t.me/FKS_UC\n"
            "🔹 Asosiy kanal: https://t.me/FKS_UZ\n"
            "💬 Admin: @FKS_PUBGM"
        )
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🌐 UC Server kanali", url="https://t.me/FKS_UC"),
            types.InlineKeyboardButton("📢 Asosiy kanal", url="https://t.me/FKS_UZ"),
            types.InlineKeyboardButton("💬 Admin bilan bog'lanish", url="https://t.me/FKS_PUBGM")
        )
        bot.send_message(message.chat.id, help_text, reply_markup=markup, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    data = call.data or ""
    if not (data.startswith("approve_") or data.startswith("reject_")):
        return

    action, target_user_id, order_id = data.split("_", 2)
    now = get_uzbekistan_time().strftime("%Y-%m-%d %H:%M")

    # Atomic PostgreSQL transaction: only one admin click can process this order.
    try:
        with db_connect() as conn:
            order = conn.execute(
                "SELECT * FROM orders WHERE order_id = %s AND user_id = %s FOR UPDATE",
                (order_id, int(target_user_id))
            ).fetchone()

            if not order:
                bot.answer_callback_query(call.id, "Buyurtma topilmadi.", show_alert=True)
                return

            if order["status"] != "Kutilmoqda ⏳":
                bot.answer_callback_query(
                    call.id, "Bu buyurtma avval ko'rib chiqilgan!", show_alert=True
                )
                return

            if action == "approve":
                # Mark and add balance in the same transaction.
                updated = conn.execute(
                    """UPDATE orders SET status = %s, processed_at = %s
                       WHERE order_id = %s AND status = %s RETURNING amount""",
                    ("✅ Tasdiqlandi", now, order_id, "Kutilmoqda ⏳")
                ).fetchone()

                if not updated:
                    bot.answer_callback_query(call.id, "Buyurtma allaqachon ko'rib chiqilgan.")
                    return

                conn.execute("""
                    INSERT INTO users (user_id, balance, joined_date)
                    VALUES (%s, 0, %s)
                    ON CONFLICT (user_id) DO NOTHING
                """, (int(target_user_id), now))

                user = conn.execute("""
                    UPDATE users SET balance = balance + %s
                    WHERE user_id = %s
                    RETURNING balance
                """, (int(updated["amount"]), int(target_user_id))).fetchone()
                new_balance = int(user["balance"])
                amount = int(updated["amount"])

            else:
                conn.execute(
                    """UPDATE orders SET status = %s, processed_at = %s
                       WHERE order_id = %s AND status = %s""",
                    ("❌ Bekor qilindi", now, order_id, "Kutilmoqda ⏳")
                )
                amount = int(order["amount"])
                new_balance = None

    except Exception as e:
        print(f"Buyurtmani qayta ishlash xatosi: {e}")
        bot.answer_callback_query(call.id, "Xatolik yuz berdi. Qayta urinib ko'ring.", show_alert=True)
        return

    if action == "approve":
        try:
            bot.send_message(
                int(target_user_id),
                (
                    "✅ <b>Balansingiz to'ldirildi!</b>\n\n"
                    f"💰 Qo'shilgan summa: <b>{amount:,} so'm</b>\n"
                    f"💳 Yangi balans: <b>{new_balance:,} so'm</b>"
                ).replace(",", " "),
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Mijozga tasdiq xabari yuborilmadi: {e}")

        bot.answer_callback_query(call.id, "Balans to'ldirildi!")
        final_text = call.message.text + f"\n\n✅ HOLAT: TASDIQLANDI\n💰 {amount:,} so'm qo'shildi."
    else:
        try:
            bot.send_message(
                int(target_user_id),
                "❌ <b>Balans to'ldirish so'rovingiz bekor qilindi.</b>\n"
                "💰 Balansingizga pul qo'shilmadi.",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Mijozga bekor qilish xabari yuborilmadi: {e}")

        bot.answer_callback_query(call.id, "So'rov bekor qilindi.")
        final_text = call.message.text + "\n\n❌ HOLAT: BEKOR QILINDI"

    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=final_text.replace(",", " "),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Admin xabarini yangilash xatosi: {e}")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/index.html", index)
    app.router.add_get("/api/balance", api_balance)
    app.router.add_post("/api/pay", api_pay)
    app.router.add_static("/static/", path="./", name="static")

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


def run_bot():
    try:
        bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        print(f"Webhookni o'chirishda xatolik: {e}")

    while True:
        try:
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            print(f"Polling xatosi: {e}")
            import time
            time.sleep(5)


async def main():
    init_db()
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    await start_web_server()

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())

 

 
