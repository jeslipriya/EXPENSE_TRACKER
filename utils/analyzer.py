import sqlite3
from datetime import datetime

def analyze_spending(user_id, month):
    conn = sqlite3.connect('expense_data.db')
    cursor = conn.cursor()
    
    # Get total income and expenses for the month
    cursor.execute('''
        SELECT 
            COALESCE(SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END), 0) as income,
            COALESCE(SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END), 0) as expense
        FROM transactions
        WHERE user_id = ? AND strftime('%Y-%m', date) = ?
    ''', (user_id, month))
    
    total_income, total_expense = cursor.fetchone()
    savings = total_income - total_expense
    
    advice = []
    
    # Savings advice
    if savings < 0:
        advice.append("⚠️ You're spending more than you earn this month! Consider reducing expenses.")
    elif savings > 0 and savings < (0.2 * total_income):
        advice.append("💡 You're saving some money, but try to save at least 20% of your income.")
    elif savings >= (0.2 * total_income):
        advice.append("✅ Great job! You're saving a healthy portion of your income.")
    
    # Get expense breakdown by category
    cursor.execute('''
        SELECT category, SUM(amount) as total
        FROM transactions
        WHERE user_id = ? AND type = 'Expense' AND strftime('%Y-%m', date) = ?
        GROUP BY category
        ORDER BY total DESC
    ''', (user_id, month))
    
    expenses_by_category = cursor.fetchall()
    
    if expenses_by_category:
        # Check if any single category is more than 50% of expenses
        for category, amount in expenses_by_category:
            if amount > 0.5 * total_expense:
                advice.append(f"⚠️ You're spending {amount/total_expense*100:.1f}% of your expenses on '{category}'. Consider diversifying your spending.")
            
            # Generic advice for top categories
            if amount > 0.3 * total_expense:
                advice.append(f"💸 You're spending a lot on '{category}'. Maybe look for ways to reduce this expense.")
    
    # Check if there are any expenses at all
    if total_expense == 0 and total_income > 0:
        advice.append("🌟 You haven't recorded any expenses this month. Great savings!")
    
    # Check if income is zero
    if total_income == 0:
        advice.append("🔄 You haven't recorded any income this month. Don't forget to track your earnings!")
    
    return advice