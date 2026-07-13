"""
app.py

Main entry point of the Automatic Sales Report Generator.
This file builds the Streamlit interface: sidebar filters, the
"Generate Report" button, KPI cards, charts, a detailed sales table,
and export buttons for Excel and PDF.

Run it with:
    streamlit run app.py
"""

from datetime import date, timedelta

import pyarrow
import streamlit as st

# Streamlit uses PyArrow behind the scenes to send tables/charts to the browser.
# On machines with very few CPU cores, PyArrow's default multi-threading can rarely
# cause a crash. Limiting it to one thread avoids that, with no noticeable effect
# on a small project like this one.
pyarrow.set_cpu_count(1)
pyarrow.set_io_thread_count(1)

from database import (
    create_tables,
    get_all_categories,
    get_all_cities,
    get_sales_data,
    insert_sample_data,
)
from reports import (
    calculate_kpis,
    create_charts,
    export_excel,
    export_pdf,
    get_detailed_sales_table,
)
from utils import format_currency, validate_date_range


def setup_database():
    """Make sure the database, tables, and sample data exist before the app runs."""
    create_tables()
    insert_sample_data()


def show_filters():
    """Display the filter widgets in the sidebar and return the chosen values."""
    st.sidebar.header("Filters")

    default_start_date = date.today() - timedelta(days=180)
    default_end_date = date.today()

    start_date = st.sidebar.date_input("Start date", value=default_start_date)
    end_date = st.sidebar.date_input("End date", value=default_end_date)

    city_options = ["All"] + get_all_cities()
    city = st.sidebar.selectbox("City", city_options)

    category_options = ["All"] + get_all_categories()
    category = st.sidebar.selectbox("Product category", category_options)

    generate_clicked = st.sidebar.button("Generate Report", type="primary")

    return start_date, end_date, city, category, generate_clicked


def show_kpi_cards(kpis):
    """Display the four KPI cards at the top of the dashboard."""
    column_1, column_2, column_3, column_4 = st.columns(4)

    column_1.metric("Total Revenue", format_currency(kpis["total_revenue"]))
    column_2.metric("Total Sales", kpis["total_sales"])

    with column_3:
        st.metric("Best Customer", kpis["top_customer_name"])
        st.caption(f"Spent {format_currency(kpis['top_customer_amount'])}")

    with column_4:
        st.metric("Best-Selling Product", kpis["best_product_name"])
        st.caption(f"{kpis['best_product_quantity']} units sold")


def show_export_buttons(sales_dataframe, kpis, start_date, end_date):
    """Display buttons that let the user create and download the Excel and PDF reports."""
    excel_column, pdf_column = st.columns(2)

    with excel_column:
        if st.button("Export to Excel"):
            file_path = export_excel(sales_dataframe, kpis)
            if file_path:
                with open(file_path, "rb") as excel_file:
                    st.download_button(
                        "Download Excel File",
                        data=excel_file,
                        file_name="sales_report.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
            else:
                st.error("Something went wrong while creating the Excel file.")

    with pdf_column:
        if st.button("Export to PDF"):
            file_path = export_pdf(sales_dataframe, kpis, start_date, end_date)
            if file_path:
                with open(file_path, "rb") as pdf_file:
                    st.download_button(
                        "Download PDF File",
                        data=pdf_file,
                        file_name="sales_report.pdf",
                        mime="application/pdf",
                    )
            else:
                st.error("Something went wrong while creating the PDF file.")


def show_dashboard(sales_dataframe, kpis, start_date, end_date):
    """Display the KPI cards, charts, detailed sales table, and export buttons."""
    show_kpi_cards(kpis)
    st.divider()

    category_figure, city_figure = create_charts(sales_dataframe)
    chart_column_1, chart_column_2 = st.columns(2)
    with chart_column_1:
        st.subheader("Revenue by Category")
        st.pyplot(category_figure)
    with chart_column_2:
        st.subheader("Revenue by City")
        st.pyplot(city_figure)

    st.divider()

    st.subheader("Detailed Sales")
    st.dataframe(get_detailed_sales_table(sales_dataframe), width="stretch", hide_index=True)

    st.divider()

    st.subheader("Export Report")
    show_export_buttons(sales_dataframe, kpis, start_date, end_date)


def main():
    """Main entry point of the Streamlit app."""
    st.set_page_config(page_title="Automatic Sales Report Generator", layout="wide")
    st.title("Automatic Sales Report Generator")
    st.write("Choose your filters on the left, then click **Generate Report**.")

    setup_database()

    start_date, end_date, city, category, generate_clicked = show_filters()

    if not validate_date_range(start_date, end_date):
        st.sidebar.error("Start date must be before the end date.")
        return

    # Streamlit reruns this whole script on every interaction (even clicking an
    # export button below). Saving the report in session_state means it stays
    # on screen instead of disappearing the moment the user clicks something else.
    if generate_clicked:
        st.session_state["report_generated"] = True
        st.session_state["filters"] = (start_date, end_date, city, category)

    if not st.session_state.get("report_generated"):
        st.info("Choose your filters and click **Generate Report** to get started.")
        return

    saved_start_date, saved_end_date, saved_city, saved_category = st.session_state["filters"]
    sales_dataframe = get_sales_data(saved_start_date, saved_end_date, saved_city, saved_category)

    if sales_dataframe.empty:
        st.warning("No sales found for the selected filters. Try widening the date range.")
        return

    kpis = calculate_kpis(sales_dataframe)
    show_dashboard(sales_dataframe, kpis, saved_start_date, saved_end_date)


if __name__ == "__main__":
    main()
