"""
reports.py

This file takes the sales data (a pandas DataFrame coming from
database.py) and turns it into the things the dashboard needs:
- KPI numbers (calculate_kpis)
- revenue grouped by category / by city
- matplotlib charts
- an Excel export
- a PDF export
"""

import matplotlib
matplotlib.use("Agg")  # Draw charts without needing a display, which Streamlit needs

import matplotlib.pyplot as plt
import pandas as pd
from openpyxl.styles import Font
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from utils import format_currency, format_date_for_display

DETAILED_SALES_COLUMNS = [
    "sale_id", "sale_date", "customer_name", "product_name",
    "category", "quantity", "unit_price", "total_amount",
]
DETAILED_SALES_HEADERS = [
    "Sale ID", "Sale Date", "Customer", "Product",
    "Category", "Quantity", "Unit Price", "Total Amount",
]


def calculate_kpis(sales_dataframe):
    """
    Calculate the four main KPIs from the sales data: total revenue,
    total number of sales, the best-selling product, and the top customer.

    Returns a dictionary. If there is no data, returns safe default
    values instead of crashing.
    """
    if sales_dataframe.empty:
        return {
            "total_revenue": 0,
            "total_sales": 0,
            "best_product_name": "No data",
            "best_product_quantity": 0,
            "top_customer_name": "No data",
            "top_customer_amount": 0,
        }

    total_revenue = sales_dataframe["total_amount"].sum()
    total_sales = len(sales_dataframe)

    product_quantities = sales_dataframe.groupby("product_name")["quantity"].sum()
    best_product_name = product_quantities.idxmax()
    best_product_quantity = int(product_quantities.max())

    customer_totals = sales_dataframe.groupby("customer_name")["total_amount"].sum()
    top_customer_name = customer_totals.idxmax()
    top_customer_amount = customer_totals.max()

    return {
        "total_revenue": total_revenue,
        "total_sales": total_sales,
        "best_product_name": best_product_name,
        "best_product_quantity": best_product_quantity,
        "top_customer_name": top_customer_name,
        "top_customer_amount": top_customer_amount,
    }


def get_revenue_by_category(sales_dataframe):
    """Return a DataFrame with total revenue grouped by product category."""
    if sales_dataframe.empty:
        return pd.DataFrame(columns=["Category", "Total Revenue"])

    result = sales_dataframe.groupby("category")["total_amount"].sum().reset_index()
    result.columns = ["Category", "Total Revenue"]
    return result.sort_values("Total Revenue", ascending=False).reset_index(drop=True)


def get_revenue_by_city(sales_dataframe):
    """Return a DataFrame with total revenue grouped by customer city."""
    if sales_dataframe.empty:
        return pd.DataFrame(columns=["City", "Total Revenue"])

    result = sales_dataframe.groupby("city")["total_amount"].sum().reset_index()
    result.columns = ["City", "Total Revenue"]
    return result.sort_values("Total Revenue", ascending=False).reset_index(drop=True)


def get_detailed_sales_table(sales_dataframe):
    """Return the sales data with only the columns (and friendly names) needed for display."""
    if sales_dataframe.empty:
        return pd.DataFrame(columns=DETAILED_SALES_HEADERS)

    detailed_table = sales_dataframe[DETAILED_SALES_COLUMNS].copy()
    detailed_table.columns = DETAILED_SALES_HEADERS
    return detailed_table


def create_charts(sales_dataframe):
    """
    Build two simple matplotlib bar charts: revenue by category and
    revenue by city. Returns the two figures so app.py can display them.
    """
    revenue_by_category = get_revenue_by_category(sales_dataframe)
    revenue_by_city = get_revenue_by_city(sales_dataframe)

    category_figure, category_axis = plt.subplots(figsize=(6, 4))
    category_axis.bar(revenue_by_category["Category"], revenue_by_category["Total Revenue"], color="#4C72B0")
    category_axis.set_title("Revenue by Category")
    category_axis.set_xlabel("Category")
    category_axis.set_ylabel("Revenue ($)")
    plt.setp(category_axis.get_xticklabels(), rotation=30, ha="right")
    category_figure.tight_layout()

    city_figure, city_axis = plt.subplots(figsize=(6, 4))
    city_axis.bar(revenue_by_city["City"], revenue_by_city["Total Revenue"], color="#55A868")
    city_axis.set_title("Revenue by City")
    city_axis.set_xlabel("City")
    city_axis.set_ylabel("Revenue ($)")
    plt.setp(city_axis.get_xticklabels(), rotation=30, ha="right")
    city_figure.tight_layout()

    return category_figure, city_figure


def export_excel(sales_dataframe, kpis, file_path="sales_report.xlsx"):
    """
    Export the report to an Excel file with four sheets: KPI summary,
    revenue by category, revenue by city, and detailed sales.
    Returns the file path on success, or None if something went wrong.
    """
    try:
        revenue_by_category = get_revenue_by_category(sales_dataframe)
        revenue_by_city = get_revenue_by_city(sales_dataframe)
        detailed_sales = get_detailed_sales_table(sales_dataframe)

        kpi_dataframe = pd.DataFrame({
            "KPI": ["Total Revenue", "Total Sales", "Best-Selling Product", "Top Customer"],
            "Value": [
                kpis["total_revenue"],
                kpis["total_sales"],
                f"{kpis['best_product_name']} ({kpis['best_product_quantity']} units)",
                f"{kpis['top_customer_name']} ({format_currency(kpis['top_customer_amount'])})",
            ],
        })

        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            kpi_dataframe.to_excel(writer, sheet_name="KPI Summary", index=False)
            revenue_by_category.to_excel(writer, sheet_name="Revenue by Category", index=False)
            revenue_by_city.to_excel(writer, sheet_name="Revenue by City", index=False)
            detailed_sales.to_excel(writer, sheet_name="Detailed Sales", index=False)

            # Bold the header row on every sheet, using openpyxl directly
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for header_cell in worksheet[1]:
                    header_cell.font = Font(bold=True)

        return file_path
    except Exception as error:
        print(f"Error while exporting Excel file: {error}")
        return None


def _build_pdf_table(rows):
    """Small helper that builds a simply-styled reportlab table from a list of rows."""
    table = Table(rows)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4C72B0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def export_pdf(sales_dataframe, kpis, start_date, end_date, file_path="sales_report.pdf"):
    """
    Export a simple one-page-style PDF report with the title, selected
    period, KPI summary, revenue by category, and revenue by city.
    Returns the file path on success, or None if something went wrong.
    """
    try:
        revenue_by_category = get_revenue_by_category(sales_dataframe)
        revenue_by_city = get_revenue_by_city(sales_dataframe)

        document = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("Sales Report", styles["Title"]))
        elements.append(Spacer(1, 6))
        period_text = f"Period: {format_date_for_display(start_date)} to {format_date_for_display(end_date)}"
        elements.append(Paragraph(period_text, styles["Normal"]))
        elements.append(Spacer(1, 16))

        kpi_rows = [
            ["KPI", "Value"],
            ["Total Revenue", format_currency(kpis["total_revenue"])],
            ["Total Sales", str(kpis["total_sales"])],
            ["Best-Selling Product", f"{kpis['best_product_name']} ({kpis['best_product_quantity']} units)"],
            ["Top Customer", f"{kpis['top_customer_name']} ({format_currency(kpis['top_customer_amount'])})"],
        ]
        elements.append(KeepTogether([
            Paragraph("KPI Summary", styles["Heading2"]),
            Spacer(1, 6),
            _build_pdf_table(kpi_rows),
        ]))
        elements.append(Spacer(1, 20))

        category_rows = [["Category", "Total Revenue"]]
        for _, row in revenue_by_category.iterrows():
            category_rows.append([row["Category"], format_currency(row["Total Revenue"])])
        elements.append(KeepTogether([
            Paragraph("Revenue by Category", styles["Heading2"]),
            Spacer(1, 6),
            _build_pdf_table(category_rows),
        ]))
        elements.append(Spacer(1, 20))

        city_rows = [["City", "Total Revenue"]]
        for _, row in revenue_by_city.iterrows():
            city_rows.append([row["City"], format_currency(row["Total Revenue"])])
        elements.append(KeepTogether([
            Paragraph("Revenue by City", styles["Heading2"]),
            Spacer(1, 6),
            _build_pdf_table(city_rows),
        ]))

        document.build(elements)
        return file_path
    except Exception as error:
        print(f"Error while exporting PDF file: {error}")
        return None
