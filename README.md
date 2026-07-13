# Automatic Sales Report Generator

A small dashboard that reads sales data from a SQLite database, lets you
filter it by date, city, and product category, and generates KPIs, charts,
and downloadable Excel/PDF reports. Built with **Python**, **SQLite**, and
**Streamlit**.

This project was built as a learning exercise. It's meant to be simple to
read and easy to extend, not a production system.

## Features

- Filter sales by date range, city, and product category
- Dashboard with 4 KPI cards: Total Revenue, Total Sales, Best Customer,
  Best-Selling Product
- Bar charts for revenue by category and revenue by city
- A detailed, sortable sales table
- One-click export to a formatted **Excel** file (`sales_report.xlsx`)
- One-click export to a simple **PDF** report (`sales_report.pdf`)
- Sample data (customers, products, and 30-100 sales) is generated
  automatically the first time you run the app

## Project Structure

```
sales_report_generator/
├── app.py             # Streamlit interface (filters, dashboard, export buttons)
├── database.py        # SQLite connection, table creation, sample data, queries
├── reports.py         # KPI calculations, charts, Excel/PDF export
├── utils.py           # Small formatting/validation helpers
├── company.db         # SQLite database (auto-created if missing)
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## How It Works

1. **`database.py`** creates three tables — `customers`, `products`, and
   `sales` — and fills them with fictional sample data the first time the
   app runs. `get_sales_data()` runs a single SQL query that joins all
   three tables and applies whichever filters were chosen in the sidebar.
2. **`app.py`** is the Streamlit page. It shows the filters, calls into
   `database.py` to get the filtered data, and calls into `reports.py` to
   turn that data into KPIs, charts, and tables.
3. **`reports.py`** takes the sales data (a pandas DataFrame) and computes
   KPIs, groups revenue by category/city, draws matplotlib bar charts, and
   builds the Excel and PDF files.
4. **`utils.py`** holds small helpers, like formatting a number as
   `$1,234.56`, that are used in more than one file.

## Setup

**1. Create a virtual environment (recommended)**

```bash
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
```

**2. Install the dependencies**

```bash
pip install -r requirements.txt
```

**3. Run the app**

```bash
streamlit run app.py
```

Your browser should open automatically at `http://localhost:8501`. The
first time you run it, `company.db` is created and filled with sample data
automatically — you don't need to do anything else.

## Using the App

1. Pick a **start date**, **end date**, **city**, and **product category**
   in the sidebar (leave city/category as "All" to include everyone).
2. Click **Generate Report**.
3. The dashboard appears with KPI cards, two bar charts, and a detailed
   sales table.
4. Click **Export to Excel** or **Export to PDF**, then use the
   **Download** button that appears to save the file.

## What It Actually Prints (Default Filters, Real Run)

Here's a real run of the app with the default filters (last 180 days, all
cities, all categories) against the sample data included in `company.db`.
Since the sample data uses random quantities/dates and is relative to
"today," your own numbers will differ slightly — but the shape of the
output will look like this.

**KPI cards:**

| KPI | Value |
|---|---|
| Total Revenue | $10,024.24 |
| Total Sales | 44 |
| Best Customer | Lucas Nunes *(spent $1,316.95)* |
| Best-Selling Product | Bluetooth Headphones *(19 units sold)* |

**Revenue by Category:**

| Category | Total Revenue |
|---|---|
| Electronics | $4,456.50 |
| Clothing | $2,734.64 |
| Home & Kitchen | $1,582.10 |
| Sports | $1,251.00 |

**Revenue by City** (top 5 of 10):

| City | Total Revenue |
|---|---|
| Chicago | $2,421.75 |
| Austin | $1,192.35 |
| Miami | $1,151.76 |
| Denver | $1,146.20 |
| Houston | $1,039.99 |

**Detailed Sales table** (44 rows, newest first — first few shown):

| Sale ID | Date | Customer | Product | Category | Qty | Unit Price | Total |
|---|---|---|---|---|---|---|---|
| 39 | 2026-07-13 | Gabriela Lima | Cotton T-Shirt | Clothing | 4 | $24.99 | $99.96 |
| 7 | 2026-07-12 | Hugo Ferreira | Tennis Racket | Sports | 3 | $99.90 | $299.70 |
| 36 | 2026-07-11 | Isabela Ramos | Winter Jacket | Clothing | 5 | $149.99 | $749.95 |

Clicking **Export to Excel** or **Export to PDF** turns this same data into
a downloadable `sales_report.xlsx` or `sales_report.pdf`.

## A Note on Dependency Versions

`requirements.txt` pins `pandas` to the 2.x series and `pyarrow` to
version 17. This isn't just being cautious — while building this project,
newer pandas/pyarrow versions caused Streamlit to crash intermittently
when rendering tables. Sticking to these tested versions avoids that.
If you ever bump these dependencies, re-test the dashboard (especially the
detailed sales table) before relying on it.
