import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import sqlite3
import os

def generate_graph(user_id, month):
    conn = sqlite3.connect('expense_data.db')
    cursor = conn.cursor()
    
    # Get daily data
    cursor.execute('''
        SELECT 
            date,
            SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END) as income,
            SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END) as expense,
            SUM(CASE WHEN type = 'Savings' THEN amount ELSE 0 END) as savings
        FROM transactions
        WHERE user_id = ? AND strftime('%Y-%m', date) = ?
        GROUP BY date
        ORDER BY date
    ''', (user_id, month))
    
    data = cursor.fetchall()
    
    if not data:
        return None
    
    dates = [row[0][-2:] for row in data]  # Get just the day part
    income = [row[1] for row in data]
    expenses = [row[2] for row in data]
    savings = [row[3] for row in data]
    
    # Calculate cumulative values
    cum_income = []
    cum_expenses = []
    cum_savings = []
    cum_balance = []
    total_i = 0
    total_e = 0
    total_s = 0
    
    for i, e, s in zip(income, expenses, savings):
        total_i += i
        total_e += e
        total_s += s
        cum_income.append(total_i)
        cum_expenses.append(total_e)
        cum_savings.append(total_s)
        cum_balance.append(total_i - total_e - total_s)
    
    # Create figure
    plt.figure(figsize=(10, 6))
    
    # Plot with thicker lines
    plt.plot(dates, cum_income, label='Income', color='green', linewidth=2)
    plt.plot(dates, cum_expenses, label='Expenses', color='red', linewidth=2)
    plt.plot(dates, cum_savings, label='Savings', color='blue', linewidth=2)
    plt.plot(dates, cum_balance, label='Balance', color='purple', linewidth=2, linestyle='--')
    
    # Style the plot
    plt.title(f'Financial Overview - {datetime.strptime(month, "%Y-%m").strftime("%B %Y")}')
    plt.xlabel('Day of Month')
    plt.ylabel('Amount (₹)')
    plt.legend()
    plt.grid(True)
    
    # Save the plot
    os.makedirs('static/graphs', exist_ok=True)
    graph_path = f'static/graphs/graph_{user_id}_{month}.png'
    plt.savefig(graph_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return f'graphs/graph_{user_id}_{month}.png'