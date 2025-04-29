import sqlite3

def filter_data(user_id, start_date, end_date, category=None):
    conn = sqlite3.connect('expense_data.db')
    cursor = conn.cursor()
    
    query = '''
        SELECT type, amount, category, date 
        FROM transactions 
        WHERE user_id = ? AND date BETWEEN ? AND ?
    '''
    params = [user_id, start_date, end_date]
    
    if category:
        query += ' AND category = ?'
        params.append(category)
    
    query += ' ORDER BY date'
    
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    
    # Convert to list of dictionaries for easier handling
    result = []
    for row in rows:
        result.append({
            'type': row[0],
            'amount': row[1],
            'category': row[2],
            'date': row[3]
        })
    
    return result