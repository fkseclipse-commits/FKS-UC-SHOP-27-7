from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Ma'lumotlar bazasidagi balansni yangilash funksiyasi
def update_user_balance(telegram_id, amount):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = balance + ? WHERE telegram_id = ?', (amount, telegram_id))
    conn.commit()
    conn.close()

# --- CLICK WEBHOOK ---
@app.route('/click/webhook', methods=['POST'])
def click_webhook():
    data = request.form.to_dict() or request.json
    
    action = data.get('action')
    amount = float(data.get('amount', 0))
    merchant_trans_id = data.get('merchant_trans_id') # Bu yerda foydalanuvchining Telegram ID si keladi
    
    if action == 1: # To'lov muvaffaqiyatli yakunlanganda
        try:
            telegram_id = int(merchant_trans_id)
            update_user_balance(telegram_id, amount)
            return jsonify({"error": 0, "error_note": "Success"})
        except Exception as e:
            return jsonify({"error": -1, "error_note": str(e)})
            
    return jsonify({"error": 0, "error_note": "OK"})

# --- PAYME WEBHOOK ---
@app.route('/payme/webhook', methods=['POST'])
def payme_webhook():
    data = request.json
    # Payme so'rovlarini qabul qilish qismi
    return jsonify({"result": {"status": 1}})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
 
