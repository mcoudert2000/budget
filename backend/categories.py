import sqlite3
from datetime import datetime
from enum import Enum
import sqlglot


class Category(str, Enum):
    NEEDS = "NEEDS"
    GROCERIES = "GROCERIES"
    SHOPPING = "SHOPPING"
    PERSONAL_CARE = "PERSONAL_CARE"
    TRANSPORT = "TRANSPORT"
    TRANSFERS = "TRANSFERS"
    BILLS = "BILLS"
    TRAVEL = "TRAVEL"
    EATING_OUT = "EATING_OUT"
    INCOME = "INCOME"
    ENTERTAINMENT = "ENTERTAINMENT"
    EMERGENCY_FUND = "EMERGENCY_FUND"
    CHARITY = "CHARITY"
    GIFTS = "GIFTS"
    LISA = "LISA"
    ISA = "ISA"
    TAX = "TAX"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def __missing__(cls, key):
        return cls.UNKNOWN


    @classmethod
    def guess_category(cls, description: str):
        cleaned = description.lower().replace(' ', '')
        if any(substring in cleaned for substring in
               ['amazon', 'waterstones', 'houseofbooks', 'amznmktplace', 'etika', 'oxfam', 'hardware', 'b&q', 'googlegoogle', 'dunelm', 'book']):
            return cls.SHOPPING
        elif any(substring in cleaned for substring in
                 ['tesco', 'sainsbur', 'waitro', 'm&s', 'co-op', 'crouchhillsupermarket', 'wmmor', 'morris', 'lidl', 'groceries', 'co-pp']):
            return cls.GROCERIES
        elif any(substring in cleaned for substring in ['tfl', 'humanforest', 'transportforlondon', 'lime*']):
            return cls.TRANSPORT
        elif any(substring in cleaned for substring in ['gympass', 'barber', 'sportsshoes', 'florencehickmanyoga', 'castleclim', 'londonfieldstriath', 'www.better', 'archwaycuts']):
            return cls.PERSONAL_CARE
        elif any(substring in cleaned for substring in
                 ['paymentreceived', 'payment', 'settleallbalances', 'americanexp', 'flatexpenses', 'finglandsplitwise']):
            return cls.TRANSFERS
        elif any(substring in cleaned for substring in
                 ['avanti', 'gwr', 'trainline', 'holidaypot', 'monzopremium', 'lner', 'mta', 'holid', 'fuel', 'travelinsurance']):
            return cls.TRAVEL
        elif any(substring in cleaned for substring in ['haringey', 'movingpot', 'water', 'utilities', 'health+dental', 'vodafone', 'thameswater', 'londonboroughofharingey', 'londonboroughofislington', 'counciltax', 'rent', 'virginmedia', 'arimaproperties', 'bills', 'wifi', 'waterbill']):
            return cls.BILLS
        elif any(substring in cleaned for substring in ['s&s']):
            return cls.ISA
        elif any(substring in cleaned for substring in ['gail', 'theroyalstar', 'pret']):
            return cls.EATING_OUT
        elif any(substring in cleaned for substring in ['checkout']):
            return cls.INCOME
        elif any(substring in cleaned for substring in ['christmaspot']):
            return cls.GIFTS
        return cls.UNKNOWN


CATEGORY_TYPES = [c for c in Category.__members__]


def create_table(cursor: sqlite3.Cursor):
    """
    Creates the monzo_raw table in the SQLite database.
    """
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        transaction_id TEXT PRIMARY KEY,
        user_category TEXT,
        model_category TEXT,
        model_confidence REAL,
        update_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)


def pull_transactions(cursor: sqlite3.Cursor, month: str = None, uncategorized_only: bool = True):
    print(f"Pulling transactions for {month} with uncategorized_only={uncategorized_only}")
    query = (
        sqlglot.select(
            "transaction_id",
            "strftime('%Y-%m-%d', timestamp, 'unixepoch') AS date",
            "description",
            "amount",
            "account",
            "category"
        )
        .from_("transactions_with_category")
        .where("date >= '2022-09-01'")
    )
    if uncategorized_only:
        query = query.where("category IS NULL")

    if month:
        query = query.where(f"strftime('%Y-%m', date) = '{month}'")

    query = query.order_by("timestamp DESC")

    cursor.execute(query.sql("sqlite"))
    print(query.sql("sqlite"))
    return cursor.fetchall()


def update_categories(transaction_id,  cursor: sqlite3.Cursor, model_category: str = None, model_confidence: float = None, user_category: str = None):
    if model_category and not model_confidence:
        raise ValueError("Model category requires model confidence")
    if model_confidence and not model_category:
        raise ValueError("Model confidence requires model category")
    if model_category and model_confidence:
        cursor.execute('''
                INSERT INTO categories (transaction_id, model_category, model_confidence) 
                VALUES (?, ?, ?)
                ON CONFLICT(transaction_id) DO UPDATE SET
                        model_category=excluded.model_category,
                        model_confidence=excluded.model_confidence,
                        update_timestamp=CURRENT_TIMESTAMP
                ''', (transaction_id, model_category, model_confidence))
        return
    if user_category:
        cursor.execute('''
                INSERT INTO categories (transaction_id, user_category) 
                VALUES (?, ?)
                ON CONFLICT(transaction_id) DO UPDATE SET
                        user_category=excluded.user_category,
                        update_timestamp=CURRENT_TIMESTAMP
                ''', (transaction_id, user_category))
        print(f"Updated {transaction_id} with category {user_category}")
        return
    raise ValueError("No category provided")


def run_model(transaction_id: str, description: str, cursor: sqlite3.Cursor):
    model_category = Category.guess_category(description)
    if model_category == Category.UNKNOWN:
        return False

    update_categories(transaction_id, cursor, model_category=model_category, model_confidence=1.0)
    print(f"Updated {transaction_id} with category {model_category}")
    return True


def ask_user(transaction_id: str, description: str, timestamp: int, amount: float, cursor: sqlite3.Cursor):
    print(f"Transaction: {description} at {datetime.fromtimestamp(timestamp)} for {amount}")
    print("Please enter the category:")
    for i, category in enumerate(CATEGORY_TYPES):
        print(f"{i + 1}: {category}")
    category = input()
    if category.isdigit() and 1 <= int(category) < len(CATEGORY_TYPES) + 1:
        update_categories(transaction_id, cursor, user_category=CATEGORY_TYPES[int(category) - 1])
        return True
    print("Invalid category")
    return False



if __name__ == '__main__':
    conn = sqlite3.connect('../db/transactions.db')
    cursor = conn.cursor()

    results = [run_model(tx[0], tx[2], cursor) for tx in pull_transactions(cursor)]
    print(f"Updated {sum(results)} transactions")
    print(f"Model couldn't classify {len(results) - sum(results)} transactions")

    user_classified = []
    try:
        for tx in pull_transactions(cursor):
            print(tx)
            user_classified.append(ask_user(tx[0], tx[2], tx[1], tx[3], cursor))
    except KeyboardInterrupt:
        print("Exiting")

    print(f"Updated {sum(user_classified)} transactions via user input")
    conn.commit()
    conn.close()