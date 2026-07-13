"""
database.py

Everything related to talking to the SQLite database lives in this file:
- connecting to the database file
- creating the tables
- filling the tables with sample data (so the app has something to show)
- reading sales data back out, with optional filters

Keeping all the database logic in one place makes it easy to find and
change later, without having to touch the Streamlit interface code.
"""

import random
import sqlite3
from datetime import date, timedelta

import pandas as pd

DATABASE_NAME = "company.db"


def connect_database():
    """Open and return a connection to the SQLite database file."""
    connection = sqlite3.connect(DATABASE_NAME)
    return connection


def create_tables():
    """Create the customers, products, and sales tables if they don't exist yet."""
    try:
        connection = connect_database()
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                city TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                sale_date TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        """)

        connection.commit()
        connection.close()
    except sqlite3.Error as error:
        print(f"Error while creating tables: {error}")


def insert_sample_data():
    """
    Fill the database with fictional but realistic-looking data.

    This only inserts data the first time it runs (when the customers
    table is still empty), so restarting the app does not create
    duplicate rows.
    """
    connection = connect_database()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM customers")
    customer_count = cursor.fetchone()[0]

    if customer_count > 0:
        connection.close()
        return

    try:
        # A fixed random seed keeps the sample data the same every time the
        # database is rebuilt, which makes it easier to test and debug.
        random.seed(42)

        customers = [
            ("Ana Silva", "New York"),
            ("Bruno Costa", "Los Angeles"),
            ("Carla Souza", "Chicago"),
            ("Diego Alves", "Houston"),
            ("Elisa Martins", "Miami"),
            ("Fabio Rocha", "Seattle"),
            ("Gabriela Lima", "Boston"),
            ("Hugo Ferreira", "Denver"),
            ("Isabela Ramos", "Austin"),
            ("Joao Pereira", "Portland"),
            ("Karina Dias", "New York"),
            ("Lucas Nunes", "Chicago"),
            ("Mariana Teixeira", "Miami"),
            ("Nelson Barros", "Houston"),
            ("Olivia Cardoso", "Seattle"),
        ]

        products = [
            ("Wireless Mouse", "Electronics", 25.90),
            ("Mechanical Keyboard", "Electronics", 89.90),
            ("USB-C Charger", "Electronics", 19.50),
            ("Bluetooth Headphones", "Electronics", 129.90),
            ("Smartwatch", "Electronics", 199.00),
            ("Cotton T-Shirt", "Clothing", 24.99),
            ("Denim Jeans", "Clothing", 59.99),
            ("Running Shoes", "Clothing", 89.99),
            ("Winter Jacket", "Clothing", 149.99),
            ("Wool Socks", "Clothing", 9.99),
            ("Coffee Maker", "Home & Kitchen", 49.90),
            ("Non-Stick Frying Pan", "Home & Kitchen", 34.90),
            ("Blender", "Home & Kitchen", 59.90),
            ("Ceramic Dinner Set", "Home & Kitchen", 79.90),
            ("Table Lamp", "Home & Kitchen", 29.90),
            ("Yoga Mat", "Sports", 22.90),
            ("Dumbbell Set", "Sports", 69.90),
            ("Soccer Ball", "Sports", 27.90),
            ("Tennis Racket", "Sports", 99.90),
            ("Water Bottle", "Sports", 14.90),
        ]

        cursor.executemany("INSERT INTO customers (name, city) VALUES (?, ?)", customers)
        cursor.executemany(
            "INSERT INTO products (name, category, price) VALUES (?, ?, ?)", products
        )
        connection.commit()

        # Look up the ids that SQLite just assigned, so sales can reference them
        cursor.execute("SELECT id FROM customers")
        customer_ids = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT id FROM products")
        product_ids = [row[0] for row in cursor.fetchall()]

        number_of_sales = random.randint(30, 100)
        today = date.today()

        sales = []
        for _ in range(number_of_sales):
            customer_id = random.choice(customer_ids)
            product_id = random.choice(product_ids)
            quantity = random.randint(1, 5)
            days_ago = random.randint(0, 180)  # sometime in the last ~6 months
            sale_date = (today - timedelta(days=days_ago)).isoformat()
            sales.append((customer_id, product_id, quantity, sale_date))

        cursor.executemany(
            """INSERT INTO sales (customer_id, product_id, quantity, sale_date)
               VALUES (?, ?, ?, ?)""",
            sales,
        )

        connection.commit()
        connection.close()
    except sqlite3.Error as error:
        print(f"Error while inserting sample data: {error}")
        connection.close()


def get_sales_data(start_date=None, end_date=None, city=None, category=None):
    """
    Return sales data as a pandas DataFrame, joined with customer and
    product details, optionally filtered by date range, city, and category.

    Any filter left as None (or "All") is simply not applied.
    Returns an empty DataFrame if something goes wrong or no rows match.
    """
    query = """
        SELECT
            sales.id AS sale_id,
            sales.sale_date,
            customers.name AS customer_name,
            customers.city,
            products.name AS product_name,
            products.category,
            sales.quantity,
            products.price AS unit_price,
            ROUND(sales.quantity * products.price, 2) AS total_amount
        FROM sales
        JOIN customers ON sales.customer_id = customers.id
        JOIN products ON sales.product_id = products.id
        WHERE 1 = 1
    """
    parameters = []

    if start_date:
        query += " AND sales.sale_date >= ?"
        parameters.append(str(start_date))

    if end_date:
        query += " AND sales.sale_date <= ?"
        parameters.append(str(end_date))

    if city and city != "All":
        query += " AND customers.city = ?"
        parameters.append(city)

    if category and category != "All":
        query += " AND products.category = ?"
        parameters.append(category)

    query += " ORDER BY sales.sale_date DESC"

    try:
        connection = connect_database()
        sales_dataframe = pd.read_sql_query(query, connection, params=parameters)
        connection.close()
    except sqlite3.Error as error:
        print(f"Error while reading sales data: {error}")
        sales_dataframe = pd.DataFrame()

    return sales_dataframe


def get_all_cities():
    """Return a sorted list of every distinct customer city, for the filter dropdown."""
    connection = connect_database()
    cursor = connection.cursor()
    cursor.execute("SELECT DISTINCT city FROM customers ORDER BY city")
    cities = [row[0] for row in cursor.fetchall()]
    connection.close()
    return cities


def get_all_categories():
    """Return a sorted list of every distinct product category, for the filter dropdown."""
    connection = connect_database()
    cursor = connection.cursor()
    cursor.execute("SELECT DISTINCT category FROM products ORDER BY category")
    categories = [row[0] for row in cursor.fetchall()]
    connection.close()
    return categories


if __name__ == "__main__":
    # Running "python database.py" directly sets up the database on its own,
    # which is handy for testing without starting the full Streamlit app.
    create_tables()
    insert_sample_data()
    print(f"Database '{DATABASE_NAME}' is ready.")
