from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime
from utils.graph import generate_graph
from utils.analyzer import analyze_spending
from utils.filters import filter_data
import os
from collections import defaultdict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'awsedrftgyhujikolp')
app.config['VERSION'] = str(datetime.now().timestamp())

# PostgreSQL configuration
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'database': os.getenv('POSTGRES_DB', 'expense_tracker'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'Jeslipriya07'),
    'port': os.getenv('POSTGRES_PORT', '5432')
}

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL database: {e}")
        raise

def init_db():
    """Initializes the database tables."""
    commands = (
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            type VARCHAR(10) NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            category VARCHAR(50) NOT NULL,
            date DATE NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER PRIMARY KEY,
            full_name VARCHAR(100),
            email VARCHAR(100),
            phone VARCHAR(20),
            address TEXT,
            currency VARCHAR(3) DEFAULT '₹',
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """
    )
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        for command in commands:
            cursor.execute(command)
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        print(f"Error creating database tables: {e}")
        raise

# Initialize database
init_db()

# Database helper functions
def get_user_id(username):
    """Gets user ID by username."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
        result = cursor.fetchone()
        return result[0] if result else None
    except psycopg2.Error as e:
        print(f"Error getting user ID: {e}")
        return None
    finally:
        if conn:
            cursor.close()
            conn.close()

# Auth routes
@app.route('/', methods=['GET', 'POST'])
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        action = request.form.get('action')
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if action == 'login':
                cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
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
                    cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', 
                                 (username, hashed_password))
                    conn.commit()
                    flash('Registration successful! Please login.')
                except psycopg2.IntegrityError:
                    flash('Username already exists')
                except psycopg2.Error as e:
                    flash('Registration failed. Please try again.')
                    print(f"Registration error: {e}")
        except psycopg2.Error as e:
            print(f"Database error: {e}")
            flash('An error occurred. Please try again.')
        finally:
            if conn:
                cursor.close()
                conn.close()
    
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
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current month income
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) 
            FROM transactions 
            WHERE user_id = %s AND type = 'Income' AND to_char(date, 'YYYY-MM') = %s
        ''', (user_id, current_month))
        income = cursor.fetchone()[0] or 0
        
        # Get current month expenses
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) 
            FROM transactions 
            WHERE user_id = %s AND type = 'Expense' AND to_char(date, 'YYYY-MM') = %s
        ''', (user_id, current_month))
        expenses = cursor.fetchone()[0] or 0
        
        # Get current month savings
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) 
            FROM transactions 
            WHERE user_id = %s AND type = 'Savings' AND to_char(date, 'YYYY-MM') = %s
        ''', (user_id, current_month))
        savings = cursor.fetchone()[0] or 0
        
        # Calculate balance (Income - Expenses - Savings)
        balance = max(0, float(income) - float(expenses) - float(savings))
        
        # Get proper outstanding balance (all previous months)
        cursor.execute('''
            SELECT 
            COALESCE(SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN type IN ('Expense', 'Savings') THEN amount ELSE 0 END), 0)
            FROM transactions
            WHERE user_id = %s
        ''', (user_id,))
        income, outflow = cursor.fetchone()
        outstanding = max(outflow - income, 0)

        # For currency symbol
        cursor.execute('SELECT currency FROM profiles WHERE user_id = %s', (user_id,))
        currency_result = cursor.fetchone()
        currency = currency_result[0] if currency_result else '₹'
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        flash('An error occurred while fetching dashboard data.')
        income = expenses = savings = balance = outstanding = 0
        currency = '₹'
    finally:
        if conn:
            cursor.close()
            conn.close()
    
    advice = analyze_spending(user_id, current_month)
    
    return render_template('dashboard.html', 
                         graph_path=graph_path,
                         income=income,
                         expenses=expenses,
                         savings=savings,
                         balance=balance,
                         outstanding=outstanding,
                         advice=advice,
                         config=app.config,
                         currency=currency)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        currency = request.form.get('currency', '₹')
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Check if profile exists
            cursor.execute('SELECT 1 FROM profiles WHERE user_id = %s', (user_id,))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing profile
                cursor.execute('''
                    UPDATE profiles 
                    SET full_name = %s, email = %s, phone = %s, address = %s, currency = %s
                    WHERE user_id = %s
                ''', (full_name, email, phone, address, currency, user_id))
            else:
                # Insert new profile
                cursor.execute('''
                    INSERT INTO profiles (user_id, full_name, email, phone, address, currency)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (user_id, full_name, email, phone, address, currency))
            
            conn.commit()
            flash('Profile updated successfully!')
            return redirect(url_for('profile'))
        except psycopg2.Error as e:
            print(f"Database error: {e}")
            flash('An error occurred while updating profile.')
        finally:
            if conn:
                cursor.close()
                conn.close()
    
    # GET request - load existing profile
    profile = {
        'full_name': '',
        'email': '',
        'phone': '',
        'address': '',
        'currency': '₹'
    }
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)
        cursor.execute('SELECT * FROM profiles WHERE user_id = %s', (user_id,))
        profile_data = cursor.fetchone()
    
        if profile_data:
            profile = {
                'full_name': profile_data['full_name'],
                'email': profile_data['email'],
                'phone': profile_data['phone'],
                'address': profile_data['address'],
                'currency': profile_data['currency']
            }
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        flash('An error occurred while loading profile data.')
    finally:
        if conn:
            cursor.close()
            conn.close()
    
    return render_template('profile.html', profile=profile)

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
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions (user_id, type, amount, category, date)
                VALUES (%s, %s, %s, %s, %s)
            ''', (user_id, trans_type, amount, category, date))
            conn.commit()
            flash('Transaction added successfully!')
            return redirect(url_for('dashboard'))
        except psycopg2.Error as e:
            print(f"Database error: {e}")
            flash('An error occurred while adding transaction.')
        finally:
            if conn:
                cursor.close()
                conn.close()
    
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
    savings = sum(t['amount'] for t in filtered_data if t['type'] == 'Savings')
    balance = income - expenses - savings

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Get user's currency
        cursor.execute('SELECT currency FROM profiles WHERE user_id = %s', (user_id,))
        currency_result = cursor.fetchone()
        currency = currency_result[0] if currency_result else '₹'
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        currency = '₹'
    finally:
        if conn:
            cursor.close()
            conn.close()

    # Group expenses by category
    category_expenses = defaultdict(float)
    for t in filtered_data:
        if t['type'] == 'Expense':
            category_expenses[t['category']] += t['amount']

    return render_template('stats_result.html',
                           income=income,
                           expenses=expenses,
                           savings=savings,
                           balance=balance,
                           start_date=start_date,
                           end_date=end_date,
                           category_expenses=dict(category_expenses),
                           category=category,
                           currency=currency)

if __name__ == '__main__':
    app.run()