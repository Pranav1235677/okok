import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import random
from faker import Faker

# Initialize Faker
fake = Faker()

# Function to generate a more realistic dataset
def generate_data(month, n=200):
    categories = [
        "Food", "Transportation", "Bills", "Groceries", "Entertainment",
        "Healthcare", "Shopping", "Travel", "Dining", "Subscriptions"
    ]
    payment_modes = [
        "Cash", "Wallet", "Credit Card", "Debit Card", "UPI", "Netbanking"
    ]
    data = []
    for _ in range(n):
        data.append({
            "Date": fake.date_this_year(),
            "Category": random.choice(categories),
            "Payment_Mode": random.choice(payment_modes),
            "Description": fake.text(max_nb_chars=30),  # Simple short descriptions
            "Amount_Paid": round(random.uniform(50.0, 1000.0), 2),
            "Cashback": round(random.uniform(0.0, 50.0), 2),
            "Month": month
        })
    return pd.DataFrame(data)

# Function to initialize the SQLite database for all months
def init_db():
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    for month in months:
        table_name = f"expenses_{month}"
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                Date TEXT,
                Category TEXT,
                Payment_Mode TEXT,
                Description TEXT,
                Amount_Paid REAL,
                Cashback REAL,
                Month TEXT
            )
        """)
    conn.commit()
    conn.close()

# Function to load data into the database for a specific month
def load_data_to_db(data, month):
    conn = sqlite3.connect('expenses.db')
    table_name = f"expenses_{month}"
    data.to_sql(table_name, conn, if_exists='append', index=False)
    conn.close()

# Function to query data from the database
def query_data(query):
    conn = sqlite3.connect('expenses.db')
    result = pd.read_sql_query(query, conn)
    conn.close()
    return result

# Extended SQL Queries
SQL_QUERIES = {
    "Total Amount Spent per Category": "SELECT Category, SUM(Amount_Paid) AS Total_Spent FROM {table_name} GROUP BY Category",
    "Monthly Spending Breakdown": "SELECT Month, SUM(Amount_Paid) AS Total_Spent FROM {table_name} GROUP BY Month",
    "Top 5 Highest Expenses": "SELECT * FROM {table_name} ORDER BY Amount_Paid DESC LIMIT 5",
    "Cashback Summary": "SELECT Payment_Mode, SUM(Cashback) AS Total_Cashback FROM {table_name} GROUP BY Payment_Mode",
    "Payment Mode Distribution": "SELECT Payment_Mode, COUNT(*) AS Transaction_Count, SUM(Amount_Paid) AS Total_Spent FROM {table_name} GROUP BY Payment_Mode",
    "Spending Trends Over Time": "SELECT Date, SUM(Amount_Paid) AS Daily_Spent FROM {table_name} GROUP BY Date ORDER BY Date",
    "Category Spending Per Payment Mode": "SELECT Category, Payment_Mode, SUM(Amount_Paid) AS Total_Spent FROM {table_name} GROUP BY Category, Payment_Mode",
    "Average Expense by Payment Mode": "SELECT Payment_Mode, AVG(Amount_Paid) AS Avg_Spending FROM {table_name} GROUP BY Payment_Mode",
    "Top 5 Categories with Highest Cashback": "SELECT Category, SUM(Cashback) AS Total_Cashback FROM {table_name} GROUP BY Category ORDER BY Total_Cashback DESC LIMIT 5",
    "Transactions Above 500": "SELECT * FROM {table_name} WHERE Amount_Paid > 500 ORDER BY Amount_Paid DESC"
}

# Main Streamlit app
st.title("Advanced Expense Tracker")

# Sidebar options
option = st.sidebar.selectbox(
    "Choose an option",
    [
        "Generate Data", "View Data", "Visualize Insights",
        "Run SQL Query", "Predefined SQL Queries"
    ]
)

if option == "Generate Data":
    st.subheader("Generate Expense Data")
    month = st.text_input("Enter the month (e.g., January):", "January")
    n = st.number_input("Enter number of records to generate:", min_value=50, max_value=1000, value=200, step=50)
    if st.button("Generate"):
        data = generate_data(month, n)
        load_data_to_db(data, month)  # Load data into the month's table
        st.success(f"Data for {month} generated and loaded into the database!")
        st.dataframe(data.head())

elif option == "View Data":
    st.subheader("View Expense Data")
    month = st.text_input("Enter the month (e.g., January):", "January")
    if st.button("View"):
        try:
            query = f"SELECT * FROM expenses_{month}"
            data = query_data(query)
            st.dataframe(data)
        except Exception as e:
            st.error(f"Error: {e}. Make sure the table for {month} exists.")

elif option == "Visualize Insights":
    st.subheader("Spending Insights")
    month = st.text_input("Enter the month (e.g., January):", "January")
    query = f"SELECT Category, SUM(Amount_Paid) AS Total_Spent FROM expenses_{month} GROUP BY Category"
    try:
        data = query_data(query)
        st.bar_chart(data.set_index("Category"))

        # Pie Chart for Spending Distribution
        fig, ax = plt.subplots()
        ax.pie(data["Total_Spent"], labels=data["Category"], autopct='%1.1f%%', startangle=140)
        ax.axis('equal')
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Error: {e}. Ensure data exists for {month}.")

elif option == "Run SQL Query":
    st.subheader("Run Custom SQL Query")
    query = st.text_area("Enter your SQL query:")
    if st.button("Execute"):
        try:
            data = query_data(query)
            st.dataframe(data)
        except Exception as e:
            st.error(f"An error occurred: {e}")

elif option == "Predefined SQL Queries":
    st.subheader("Predefined SQL Queries")
    month = st.text_input("Enter the month (e.g., January):", "January")
    query_name = st.selectbox("Select a query to run", list(SQL_QUERIES.keys()))
    query = SQL_QUERIES[query_name].replace("{table_name}", f"expenses_{month}")
    if st.button("Run Query"):
        try:
            data = query_data(query)
            st.dataframe(data)
            # Specific visualizations for some queries
            if query_name in ["Spending Trends Over Time"]:
                st.line_chart(data.set_index("Date"))
            elif query_name in ["Total Amount Spent per Category", "Payment Mode Distribution"]:
                st.bar_chart(data.set_index(data.columns[0]))
        except Exception as e:
            st.error(f"Error: {e}. Ensure data exists for {month}.")

# Initialize the database
init_db()