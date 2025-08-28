import sqlite3
import requests
from flask import Flask, request, jsonify
import json
import datetime
from datetime import timedelta
import jalali_date

# --- تنظیمات ---
BOT_API_TOKEN = "1946785359:Za2gLFhRyo9lQmMu4mSOERzgmKRgFN77SFvLJ6VU"
# در PythonAnywhere، APP_URL را با آدرس وب‌سایت خود جایگزین کنید
APP_URL = "http://<YourUsername>.pythonanywhere.com"

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('travel_management.db')
    conn.row_factory = sqlite3.Row
    return conn

def send_message(chat_id, text):
    url = f"https://api.bale.ai/bot{BOT_API_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    message = data['message']
    chat_id = message['chat']['id']
    text = message['text']

    conn = get_db_connection()
    cursor = conn.cursor()

    if text.startswith('/start'):
        send_message(chat_id, "لطفاً برای احراز هویت، شماره تلفن خود را به صورت زیر ارسال کنید: \nمثال: `09121234567`")
        return jsonify({'status': 'ok'})
    
    if text.startswith('09') and len(text) == 11:
        phone_number = text.strip()
        
        cursor.execute("SELECT * FROM people WHERE phone_number = ?", (phone_number,))
        person = cursor.fetchone()
        
        if person:
            if person['is_verified'] == 1:
                send_message(chat_id, "شما قبلاً احراز هویت شده‌اید.")
            else:
                cursor.execute("UPDATE people SET baale_id = ?, is_verified = 1 WHERE id = ?", (chat_id, person['id']))
                conn.commit()
                
                entry_date_obj = datetime.datetime.strptime(person['entry_date'], '%Y-%m-%d').date()
                exit_date_obj = entry_date_obj + timedelta(days=30)
                jalali_exit_date = jalali_date.Gregorian(exit_date_obj.year, exit_date_obj.month, exit_date_obj.day).persian_date
                
                send_message(chat_id, f"✅ جناب آقای {person['full_name']}، احراز هویت شما با موفقیت انجام شد.\n"
                                        f"تاریخ ورود شما: {jalali_date.Gregorian(entry_date_obj.year, entry_date_obj.month, entry_date_obj.day).persian_date[0]}/{jalali_date.Gregorian(entry_date_obj.year, entry_date_obj.month, entry_date_obj.day).persian_date[1]}/{jalali_date.Gregorian(entry_date_obj.year, entry_date_obj.month, entry_date_obj.day).persian_date[2]}\n"
                                        f"تاریخ تقریبی خروج شما: {jalali_exit_date[0]}/{jalali_exit_date[1]}/{jalali_exit_date[2]}")
        else:
            send_message(chat_id, "شماره تلفن شما در سیستم یافت نشد. لطفاً با مسئول مربوطه تماس بگیرید.")
    
    conn.close()
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # این کد برای اجرای اپلیکیشن Flask و تنظیم webhook است
    # set_webhook_url() را یک بار اجرا کنید تا webhook تنظیم شود.
    app.run(host='0.0.0.0', port=5000)