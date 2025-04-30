# Expense Tracker Web Application

A full-stack expense management web application that allows users to track income, expenses, savings, and visualize financial data using interactive graphs. Built using **Flask**, **SQLite**, and **Matplotlib**, it offers insights and spending suggestions based on user input.

---

## Features

- ✅ Add and manage income and expenses
- 📊 Real-time dashboard displaying key financial metrics
- 📅 Date and category-based statistics with filters
- 📈 Graph-based data visualization (using Matplotlib)
- 🤖 Expense analyzer with personalized suggestions

---

## Tech Stack

| Layer         | Technology           |
|---------------|----------------------|
| Frontend      | HTML, CSS            |
| Backend       | Python (Flask)       |
| Database      | SQLite3              |
| Visualization | Matplotlib           |

---

## Project Structure
```
    EXPENSE_TRACKER/ 
    │ ├── static/ 
        │ ├── css/ 
            │ │ └── style.css 
        │ └── graphs/ 
            │ └── graph_X.png (auto-generated) 
    │ ├── templates/ 
    │ ├── base.html 
    │ ├── index.html 
    │ ├── dashboard.html 
    │ ├── add_expense.html 
    │ ├── statistics.html 
    │ └── stats_result.html 
    │ ├── utils/ 
        │ ├── analyzer.py 
        │ ├── filters.py 
        │ └── graph.py 
    │ ├── app.py 
    ├── expense_data.db (auto-gemerated)
    ├── requirements.txt 
    └── .gitignore
```

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/expense-tracker.git
cd expense-tracker

### 2. Install Dependencies

```
pip install -r requirements.txt

### 3. Run the Application
```
python app.py

Then open your browser and go to: http://127.0.0.1:5000/

### .gitignore Configuration

To prevent committing generated graphs and the SQLite database:

/static/graphs/
*.png
*.db

### Future Improvements

User authentication and login system

Export data to PDF/CSV

Monthly budgeting goals

Email reports/reminders

### License

This project is open-source and available under the MIT License.

### Author

Developed by Jesli, Computer Science Student