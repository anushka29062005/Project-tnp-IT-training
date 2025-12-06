import sqlite3
import csv
from datetime import datetime, date

#  DATABASE

class Database:
    def __init__(self, db_name="expenses.db"):
        self.conn = sqlite3.connect(db_name) 
        self.create_tables()

    def create_tables(self):
        cur = self.conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                created_at TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS categories(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                created_at TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category_id INTEGER,
                amount REAL,
                date TEXT,
                note TEXT,
                created_at TEXT
            )
        """)

        self.conn.commit()


# MODELS 

class User:
    def __init__(self, username, user_id=None):
        self.id = user_id
        self.username = username
        self.created_at = datetime.now().isoformat()

class Category:
    def __init__(self, name, category_id=None):
        self.id = category_id
        self.name = name
        self.created_at = datetime.now().isoformat()

class Expense:
    def __init__(self, user_id, category_id, amount, date, note, exp_id=None):
        self.id = exp_id
        self.user_id = user_id
        self.category_id = category_id
        self.amount = amount
        self.date = date
        self.note = note
        self.created_at = datetime.now().isoformat()


# MANAGER 

class ExpenseManager:
    def __init__(self, db):
        self.db = db

    #  USER 
    def create_user(self, username):
        cur = self.db.conn.cursor()
        cur.execute("INSERT OR IGNORE INTO users(username, created_at) VALUES(?, ?)",
                    (username, datetime.now().isoformat()))
        self.db.conn.commit()
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        return cur.fetchone()[0]

    #  CATEGORY 
    def get_or_create_category(self, name):
        cur = self.db.conn.cursor()
        cur.execute("SELECT id FROM categories WHERE name = ?", (name,))
        row = cur.fetchone()

        if row:
            return row[0]

        cur.execute("INSERT INTO categories(name, created_at) VALUES(?, ?)",
                    (name, datetime.now().isoformat()))
        self.db.conn.commit()

        return cur.lastrowid

    # ADD EXPENSE
    def add_expense(self, user_id, amount, category, date_str, note):
        category_id = self.get_or_create_category(category)
        cur = self.db.conn.cursor()
        cur.execute("""
            INSERT INTO expenses(user_id, category_id, amount, date, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, category_id, amount, date_str, note, datetime.now().isoformat()))
        self.db.conn.commit()

    # VIEW EXPENSES 
    def get_expenses(self, user_id):
        cur = self.db.conn.cursor()
        cur.execute("""
            SELECT e.id, e.date, c.name, e.amount, e.note 
            FROM expenses e 
            JOIN categories c ON e.category_id = c.id
            WHERE e.user_id = ?
            ORDER BY e.date DESC
        """, (user_id,))
        return cur.fetchall()

    #  CATEGORY SUMMARY 
    def category_summary(self, user_id):
        cur = self.db.conn.cursor()
        cur.execute("""
            SELECT c.name, SUM(e.amount) 
            FROM expenses e
            JOIN categories c ON e.category_id = c.id
            WHERE e.user_id = ?
            GROUP BY c.id
        """, (user_id,))
        return cur.fetchall()

    #  EXPORT CSV 
    def export_csv(self, user_id, filename="expenses.csv"):
        rows = self.get_expenses(user_id)
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Date", "Category", "Amount", "Note"])
            writer.writerows(rows)

    #  EXPORT TEXT REPORT 
    def export_text(self, user_id, filename="report.txt"):
        rows = self.get_expenses(user_id)
        summary = self.category_summary(user_id)

        with open(filename, "w") as f:
            f.write("Expense Report\n")
            f.write("-" * 40 + "\n\n")

            f.write("Category Summary:\n")
            for cat, amt in summary:
                f.write(f"{cat}: {amt}\n")

            f.write("\nDetailed Expenses:\n")
            for r in rows:
                f.write(f"{r}\n")


#  CLI APP 

def main():
    db = Database()
    manager = ExpenseManager(db)

    print("\n=== Smart Expense Tracker ===")
    username = input("Enter your username: ").strip()
    user_id = manager.create_user(username)

    while True:
        print("\nMenu:")
        print("1. Add Expense")
        print("2. View Expenses")
        print("3. Category Summary")
        print("4. Export CSV")
        print("5. Export Text Report")
        print("6. Exit")

        choice = input("Choose: ").strip()

        if choice == "1":
            amt = float(input("Amount: "))
            cat = input("Category: ")
            dt = input("Date (YYYY-MM-DD) (Leave empty for today): ").strip()
            dt = dt if dt else date.today().isoformat()
            note = input("Note: ")
            manager.add_expense(user_id, amt, cat, dt, note)
            print("Expense added.")

        elif choice == "2":
            rows = manager.get_expenses(user_id)
            print("\nYour Expenses:")
            for r in rows:
                print(r)

        elif choice == "3":
            summary = manager.category_summary(user_id)
            print("\nCategory Summary:")
            for c, a in summary:
                print(f"{c}: {a}")

        elif choice == "4":
            manager.export_csv(user_id)
            print("CSV Exported.")

        elif choice == "5":
            manager.export_text(user_id)
            print("Text Report Exported.")

        elif choice == "6":
            print("Goodbye!")
            break

        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
