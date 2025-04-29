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
    
    if not data:
        # Return a default empty graph
        dates = []
        income = []
        expenses = []
    else:
        dates = [row[0] for row in data]
        income = [row[1] for row in data]
        expenses = [row[2] for row in data]
    
    # Calculate cumulative values
    cum_income = []
    cum_expense = []
    cum_savings = []
    total_income = 0
    total_expense = 0
    
    for i, e in zip(income, expenses):
        total_income += i
        total_expense += e
        cum_income.append(total_income)
        cum_expense.append(total_expense)
        cum_savings.append(total_income - total_expense)
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    
    # Plot lines
    plt.plot(dates, cum_income, label='Cumulative Income', color='green', marker='o')
    plt.plot(dates, cum_expense, label='Cumulative Expenses', color='red', marker='o')
    plt.plot(dates, cum_savings, label='Savings', color='blue', marker='o')
    
    # Add title and labels
    month_name = datetime.strptime(month, '%Y-%m').strftime('%B %Y')
    plt.title(f'Financial Overview - {month_name}')
    plt.xlabel('Date')
    plt.ylabel('Amount (₹)')
    plt.legend()
    plt.grid(True)
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save the plot
    static_dir = 'static'
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    graph_filename = f'graphs/graph_{user_id}_{month}.png'
    graph_path = os.path.join(static_dir, graph_filename)
    
    graph_dir = os.path.join(static_dir, 'graphs')
    if not os.path.exists(graph_dir):
        os.makedirs(graph_dir)
    
    plt.savefig(graph_path)
    plt.close()
    
    return graph_filename