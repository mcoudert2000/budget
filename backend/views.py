import sqlite3
from contextlib import closing

AMEX_CLEANED_VIEW = """
CREATE VIEW amex_transaction_cleaned AS
SELECT 
    cast(reference as varchar) AS transaction_id,
    strftime('%s', date(substr(date, 7, 4) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2))) AS timestamp,
    description,
    -1 * amount as amount,
    address || ' ' || town_city || ' ' || postcode || ' ' || country as address,
    ingestion_timestamp
FROM amex_raw;
"""

MONZO_CLEANED_VIEW = """
CREATE VIEW monzo_transaction_cleaned AS
SELECT 
    cast(transaction_id as varchar) as transaction_id,
    strftime('%s', 
        date(substr(date, 7, 4) || '-' || 
             substr(date, 4, 2) || '-' || 
             substr(date, 1, 2) || ' ' || 
             time)) AS timestamp,  -- Combine date and time into a Unix timestamp
    name || ' ' || description || ' ' || notes_and_tags as description,
    amount,
    address as address,
    ingestion_timestamp
FROM monzo_raw;
"""

SPLITWISE_CLEANED_VIEW = """
CREATE VIEW splitwise_transaction_cleaned AS
SELECT
    cast(id as varchar) AS transaction_id,
    strftime('%s', date) AS timestamp,
    description,
    (
        SELECT
             cast(json_extract(value, '$.net_balance') as float)  -- Extract net_balance from the user
        FROM
            json_each(users)  -- Each user entry in the users JSON array
        WHERE
            json_extract(value, '$.user_id') = 51056312  -- Check for the specific user ID
    ) AS amount,
    NULL AS address,
    ingestion_timestamp
FROM
    splitwise_raw
WHERE
    deleted_at is null;
"""

UNION_TRANSACTION_VIEW = """
CREATE VIEW all_transactions AS
SELECT *, 'AMEX' as account FROM amex_transaction_cleaned
UNION ALL
SELECT *, 'MONZO' as account FROM monzo_transaction_cleaned
UNION ALL
SELECT *, 'SPLITWISE' as account FROM splitwise_transaction_cleaned;
"""

TRANSACTIONS_WITH_CATEGORY = """
CREATE VIEW transactions_with_category AS
SELECT 
    transaction_id,
    timestamp,
    description,
    amount,
    address,
    account,
    user_category,
    model_category,
    model_confidence,
    coalesce(user_category, model_category) as category  
FROM all_transactions
LEFT JOIN categories USING (transaction_id)
"""


CATEGORIES_BY_MONTH = """
CREATE VIEW monthly_category_spend AS
SELECT 
    strftime('%Y-%m', timestamp, 'unixepoch') AS month,
    category,
    ROUND(SUM(amount), 2) AS total_spend
FROM 
    transactions_with_category
GROUP BY 
    month, category
ORDER BY 
    month DESC, category;
"""



def main():
    with sqlite3.connect('transactions.db') as db:
        with closing(db.cursor()) as c:
            c.execute("DROP VIEW IF EXISTS amex_transaction_cleaned;")
            c.execute("DROP VIEW IF EXISTS monzo_transaction_cleaned;")
            c.execute("DROP VIEW IF EXISTS splitwise_transaction_cleaned;")
            c.execute("DROP VIEW IF EXISTS all_transactions;")
            c.execute("DROP VIEW IF EXISTS transactions_with_category;")
            c.execute("DROP VIEW IF EXISTS monthly_category_spend;")
            c.execute(AMEX_CLEANED_VIEW)
            c.execute(MONZO_CLEANED_VIEW)
            c.execute(SPLITWISE_CLEANED_VIEW)
            c.execute(UNION_TRANSACTION_VIEW)
            c.execute(TRANSACTIONS_WITH_CATEGORY)
            c.execute(CATEGORIES_BY_MONTH)


if __name__ == '__main__':
    main()
