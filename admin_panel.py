from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('travel_management.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_person', methods=['GET', 'POST'])
def add_person():
    conn = get_db_connection()
    if request.method == 'POST':
        full_name = request.form['full_name']
        entry_date = request.form['entry_date']
        phone_number = request.form['phone_number']
        manager_id = request.form['manager_id']
        
        conn.execute('INSERT INTO people (full_name, entry_date, phone_number, manager_id) VALUES (?, ?, ?, ?)',
                     (full_name, entry_date, phone_number, manager_id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    
    managers = conn.execute('SELECT * FROM managers').fetchall()
    conn.close()
    return render_template('add_person.html', managers=managers)

@app.route('/add_manager', methods=['GET', 'POST'])
def add_manager():
    conn = get_db_connection()
    if request.method == 'POST':
        manager_name = request.form['manager_name']
        baale_id = request.form['baale_id']
        
        conn.execute('INSERT INTO managers (manager_name, baale_id) VALUES (?, ?)',
                     (manager_name, baale_id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('add_manager.html')

if __name__ == '__main__':
    app.run(debug=True)