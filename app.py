from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime
from utils.graph import generate_graph
from utils.analyzer import analyze_spending
from utils.filters import filter_data
import os

app = Flask(__name__)
app.secret_key = 'awsedrftgyhujikolp'
DATABASE = 'expense_data.db'

# Initialize database
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        conn.commit()

init_db()

# Database helper functions
def get_db():
    return sqlite3.connect(DATABASE)

def get_user_id(username):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        return result[0] if result else None

# Auth routes
@app.route('/', methods=['GET', 'POST'])
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        action = request.form.get('action')
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            if action == 'login':
                cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
                user = cursor.fetchone()
                
                if user and check_password_hash(user[2], password):
                    session['username'] = username
                    session['user_id'] = user[0]
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid username or password')
            
            elif action == 'register':
                try:
                    hashed_password = generate_password_hash(password)
                    cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', 
                                 (username, hashed_password))
                    conn.commit()
                    flash('Registration successful! Please login.')
                except sqlite3.IntegrityError:
                    flash('Username already exists')
    
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('index'))

# Main app routes
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    current_month = datetime.now().strftime('%Y-%m')
    
    # Generate graph
    graph_path = generate_graph(user_id, current_month)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get current month income
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) 
            FROM transactions 
            WHERE user_id = ? AND type = 'Income' AND strftime('%Y-%m', date) = ?
        ''', (user_id, current_month))
        income = cursor.fetchone()[0] or 0
        
        # Get current month expenses
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) 
            FROM transactions 
            WHERE user_id = ? AND type = 'Expense' AND strftime('%Y-%m', date) = ?
        ''', (user_id, current_month))
        expenses = cursor.fetchone()[0] or 0
        
        # Calculate savings (ensure this is correct)
        savings = float(income) - float(expenses)
        
        # Get proper outstanding balance (all previous months)
        cursor.execute('''
            SELECT 
                COALESCE(SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END), 0)
            FROM transactions
            WHERE user_id = ? AND strftime('%Y-%m', date) < ?
        ''', (user_id, current_month))
        outstanding = cursor.fetchone()[0] or 0
    
    advice = analyze_spending(user_id, current_month)
    
    return render_template('dashboard.html', 
                         graph_path=graph_path,
                         income=income,
                         expenses=expenses,
                         savings=savings,
                         outstanding=outstanding,
                         advice=advice)

@app.route('/add', methods=['GET', 'POST'])
def add_expense():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        user_id = session['user_id']
        trans_type = request.form['type']
        amount = float(request.form['amount'])
        category = request.form['category']
        date = request.form['date']
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions (user_id, type, amount, category, date)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, trans_type, amount, category, date))
            conn.commit()
        
        flash('Transaction added successfully!')
        return redirect(url_for('dashboard'))
    
    return render_template('add_expense.html', datetime=datetime)

@app.route('/statistics', methods=['GET', 'POST'])
def statistics():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        user_id = session['user_id']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        category = request.form.get('category', '')
        
        return redirect(url_for('stats_result', 
                              start_date=start_date,
                              end_date=end_date,
                              category=category))
    
    return render_template('statistics.html')

@app.route('/stats_result')
def stats_result():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category = request.args.get('category', '')
    
    filtered_data = filter_data(user_id, start_date, end_date, category)
    
    income = sum(t['amount'] for t in filtered_data if t['type'] == 'Income')
    expenses = sum(t['amount'] for t in filtered_data if t['type'] == 'Expense')
    savings = income - expenses
    
    return render_template('stats_result.html',
                         income=income,
                         expenses=expenses,
                         savings=savings,
                         start_date=start_date,
                         end_date=end_date,
                         category=category)

if __name__ == '__main__':
    app.run(debug=True)