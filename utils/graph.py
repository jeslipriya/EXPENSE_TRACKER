import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import sqlite3
import os

def generate_graph(user_id, month):
    conn = sqlite3.connect('expense_data.db')
    cursor = conn.cursor()
    
    # Get daily data for the month
    cursor.execute('''
        SELECT date, 
               SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END) as income,
               SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END) as expense
        FROM transactions
        WHERE user_id = ? AND strftime('%Y-%m', date) = ?
        GROUP BY date
        ORDER BY date
    ''', (user_id, month))
    
    data = cursor.fetchall()
    
    # Prepare data
    dates = []
    daily_income = []
    daily_expense = []
    
    for row in data:
        dates.append(row[0])
        daily_income.append(row[1])
        daily_expense.append(row[2])
    
    # Calculate cumulative values
    cum_income = []
    cum_expense = []
    cum_savings = []
    total_income = 0
    total_expense = 0
    
    for i, e in zip(daily_income, daily_expense):
        total_income += i
        total_expense += e
        cum_income.append(total_income)
        cum_expense.append(total_expense)
        cum_savings.append(total_income - total_expense)
    
    # Create the plot with larger figure size
    plt.figure(figsize=(12, 8))
    
    # Plot lines with thicker lines and distinct colors
    plt.plot(dates, cum_income, label='Cumulative Income', color='#2ecc71', linewidth=3, marker='o')
    plt.plot(dates, cum_expense, label='Cumulative Expenses', color='#e74c3c', linewidth=3, marker='o')
    plt.plot(dates, cum_savings, label='Savings', color='#3498db', linewidth=3, marker='o')
    
    # Style the plot
    plt.title(f'Financial Overview - {datetime.strptime(month, "%Y-%m").strftime("%B %Y")}', fontsize=16)
    plt.xlabel('Date', fontsize=14)
    plt.ylabel('Amount (₹)', fontsize=14)
    plt.legend(fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Format x-axis
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.tight_layout()
    
    # Ensure the graphs directory exists
    graph_dir = os.path.join('static', 'graphs')
    os.makedirs(graph_dir, exist_ok=True)
    
    # Save the plot
    graph_filename = f'graphs/graph_{user_id}_{month}.png'
    graph_path = os.path.join('static', graph_filename)
    plt.savefig(graph_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return graph_filename