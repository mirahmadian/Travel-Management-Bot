import sqlite3
import requests
import datetime
from datetime import timedelta
import jalali_date
import time
import schedule

# --- تنظیمات ---
BAALE_API_TOKEN = "1946785359:Za2gLFhRyo9lQmMu4mSOERzgmKRgFN77SFvLJ6VU"
REMINDER_DAYS_BEFORE_EXIT = 5

def get_db_connection():
    conn = sqlite3.connect('travel_management.db')
    conn.row_factory = sqlite3.Row
    return conn

def setup_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS managers (
            id INTEGER PRIMARY KEY,
            manager_name TEXT NOT NULL,
            baale_id TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            entry_date TEXT NOT NULL,
            phone_number TEXT,
            baale_id TEXT,
            is_verified INTEGER DEFAULT 0,
            manager_id INTEGER,
            reminder_sent INTEGER DEFAULT 0,
            exit_date TEXT,
            FOREIGN KEY (manager_id) REFERENCES managers(id)
        )
    ''')
    conn.commit()
    conn.close()

def send_baale_message(chat_id, message):
    url = f"https://api.bale.ai/bot{BAALE_API_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"پیام با موفقیت به {chat_id} ارسال شد.")
    except requests.exceptions.RequestException as e:
        print(f"خطا در ارسال پیام به {chat_id}: {e}")

def check_reminders():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.*, m.manager_name, m.baale_id AS manager_baale_id
        FROM people p
        JOIN managers m ON p.manager_id = m.id
        WHERE p.reminder_sent = 0 AND p.is_verified = 1
    ''')
    
    people_to_check = cursor.fetchall()
    
    for person in people_to_check:
        try:
            entry_date_obj = datetime.datetime.strptime(person['entry_date'], '%Y-%m-%d').date()
            exit_date_obj = entry_date_obj + timedelta(days=30)
            
            cursor.execute("UPDATE people SET exit_date = ? WHERE id = ?", (exit_date_obj.strftime('%Y-%m-%d'), person['id']))
            conn.commit()

            today = datetime.date.today()
            days_until_exit = (exit_date_obj - today).days

            if days_until_exit == REMINDER_DAYS_BEFORE_EXIT:
                jalali_exit_date = jalali_date.Gregorian(exit_date_obj.year, exit_date_obj.month, exit_date_obj.day).persian_date
                weekdays = ["دوشنبه", "سه شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"]
                day_of_week = weekdays[exit_date_obj.weekday()]

                person_message = (
                    f"جناب آقای {person['full_name']}\n"
                    f"تاریخ خروج شما از کشور روز **{day_of_week}** مورخ **{jalali_exit_date[0]}/{jalali_exit_date[1]}/{jalali_exit_date[2]}** است. "
                    f"لطفاً به نحوی برنامه‌ریزی نمایید که حتماً در تاریخ مذکور از کشور خارج شوید."
                )
                send_baale_message(person['baale_id'], person_message)

                manager_message = (
                    f"تاریخ پایان مأموریت آقای **{person['full_name']}** تاریخ **{jalali_exit_date[0]}/{jalali_exit_date[1]}/{jalali_exit_date[2]}** است. "
                    f"لطفاً نسبت به جایگزینی وی در صورت نیاز برنامه‌ریزی لازم را بفرمایید."
                )
                send_baale_message(person['manager_baale_id'], manager_message)
                
                cursor.execute("UPDATE people SET reminder_sent = 1 WHERE id = ?", (person['id'],))
                conn.commit()
        
        except Exception as e:
            print(f"خطا در پردازش اطلاعات برای {person['full_name']}: {e}")

    conn.close()

if __name__ == "__main__":
    setup_database()
    print("اسکریپت اصلی آماده است. هر ۲۴ ساعت یکبار اجرا می‌شود.")
    schedule.every(24).hours.do(check_reminders)
    
    while True:
        schedule.run_pending()
        time.sleep(1)