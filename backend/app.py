import sqlglot

from categories import update_categories, Category, pull_transactions
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

import sqlite3
from pydantic import BaseModel
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow requests from your React app
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

class TransactionUpdate(BaseModel):
    transaction_id: str
    user_category: Category

class MultipleTransactionUpdate(BaseModel):
    transaction_ids: list[str]
    user_category: Category

class GetTransactions(BaseModel):
    month: Optional[str] = None
    uncategorized: Optional[bool] = False


def get_db_connection(is_local: bool = False):
    if is_local:
        conn = sqlite3.connect("/Users/matthew.coudert/budget/db/transactions.db")
    else:
        conn = sqlite3.connect("/db/transactions.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/transactions/")
def get_transactions(get: GetTransactions = Depends()):
    print(get)
    conn = get_db_connection()
    cursor = conn.cursor()
    transactions = pull_transactions(cursor, get.month, get.uncategorized)
    conn.close()
    return [{"transaction_id": t[0], "date": t[1], "description": t[2], "amount": t[3], "account": t[4], "category": t[5]} for t in transactions]


@app.put("/categorize/")
def categorize_transaction(update: TransactionUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    update_categories(transaction_id=update.transaction_id, cursor=cursor, user_category=update.user_category.value)
    conn.commit()
    conn.close()
    return {"message": "Transaction categorized successfully"}


@app.put("/categorize_multiple/")
def categorize_multiple_transactions(update: MultipleTransactionUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()

    num_categorized = 0

    for txn_id in update.transaction_ids:
        if update_categories(transaction_id=txn_id, cursor=cursor, user_category=update.user_category.value):
            num_categorized += 1
    conn.commit()
    conn.close()
    return {"message": f"{num_categorized} transactions categorized successfully"}

@app.put("/auto_categorize/")
def auto_categorize():
    from categories import run_model
    conn = get_db_connection()
    cursor = conn.cursor()

    transactions = pull_transactions(cursor, None, True)
    num_categorized = 0
    for transaction in transactions:
        transaction_id = transaction[0]
        description = transaction[2]
        if run_model(transaction_id, description, cursor):
            num_categorized += 1

    conn.commit()
    conn.close()
    return {"message": f"{num_categorized} transactions auto-categorized successfully"}


@app.get("/pivot_data")
def get_pivot_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            strftime('%Y-%m', timestamp, 'unixepoch') AS month,
            coalesce(category, 'UNKNOWN') AS category,
            sum(coalesce(amount, 0)) AS amount
        FROM
            transactions_with_category
        WHERE
            timestamp >= strftime('%s', '2022-08-01')
        GROUP BY
            month, category
        ORDER BY
            month DESC;
    """
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()

    # Format the data for the pivot table
    return [{"month": row[0], "category": row[1], "amount": row[2]} for row in data]


@app.get("/total")
def get_total(category: Optional[str] = None):
    query = sqlglot.select("sum(amount)").from_("transactions_with_category")
    if category:
        query = query.where(f"category = '{category}'")
    conn = get_db_connection()
    cursor = conn.cursor()

    result = cursor.execute(query.sql("sqlite")).fetchone()
    total = result['SUM(amount)'] if result['SUM(amount)'] is not None else 0

    return {"total": total}

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/full_load")
def full_load():
    from full_load import main
    main()
    return {"message": "Data loaded successfully"}


@app.get("/category_spend")
def category_spend(category: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            strftime('%Y', datetime(timestamp, 'unixepoch')) AS year,
            strftime('%m', datetime(timestamp, 'unixepoch')) AS month_number,
            strftime('%m', datetime(timestamp, 'unixepoch')) || '-' || strftime('%Y-%m', datetime(timestamp, 'unixepoch')) AS sort_key,
            CASE strftime('%m', datetime(timestamp, 'unixepoch'))
                WHEN '01' THEN 'Jan'
                WHEN '02' THEN 'Feb'
                WHEN '03' THEN 'Mar'
                WHEN '04' THEN 'Apr'
                WHEN '05' THEN 'May'
                WHEN '06' THEN 'Jun'
                WHEN '07' THEN 'Jul'
                WHEN '08' THEN 'Aug'
                WHEN '09' THEN 'Sep'
                WHEN '10' THEN 'Oct'
                WHEN '11' THEN 'Nov'
                WHEN '12' THEN 'Dec'
            END AS month,
            SUM(amount) AS amount
        FROM transactions_with_category
        WHERE category LIKE ? AND year >= '2023'
        GROUP BY year, month_number
        ORDER BY year, month_number
    """
    cursor.execute(query, (category.upper(),))
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "year": int(row["year"]),
            "month": row["month"],
            "amount": float(row["amount"])
        }
        for row in rows
    ]

