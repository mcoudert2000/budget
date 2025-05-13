import gspread
from oauth2client.service_account import ServiceAccountCredentials

from app import get_db_connection

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SPREADSHEET_KEY = "1M46p-BUbQdGPRDg-vFFqmc4YXzxM4KHVV_zrZT2zarY"

class MonzoRawTransaction:
    def __init__(self, transaction_id, date, time, trans_type, name, emoji, category, amount, currency,
                 local_amount, local_currency, notes_and_tags, address, receipt, description, category_split):
        self.transaction_id = transaction_id
        self.date = date
        self.time = time
        self.trans_type = trans_type
        self.name = name
        self.emoji = emoji
        self.category = category
        self.amount = amount
        self.currency = currency
        self.local_amount = local_amount
        self.local_currency = local_currency
        self.notes_and_tags = notes_and_tags
        self.address = address
        self.receipt = receipt
        self.description = description
        self.category_split = category_split

    def __repr__(self):
        return f"MonzoRaw({self.transaction_id}, {self.date}, {self.name})"

    @classmethod
    def create_table(cls, cursor):
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS monzo_raw (
            transaction_id TEXT PRIMARY KEY,
            date DATE,
            time TIME,
            trans_type TEXT,
            name TEXT,
            emoji TEXT,
            category TEXT,
            amount REAL,
            currency TEXT,
            local_amount REAL,
            local_currency TEXT,
            notes_and_tags TEXT,
            address TEXT,
            receipt TEXT,
            description TEXT,
            category_split TEXT,
            ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def insert(self, cursor):
        cursor.execute("""
            INSERT INTO monzo_raw (transaction_id, date, time, trans_type, name, emoji, category, amount, currency, local_amount, local_currency, notes_and_tags, address, receipt, description, category_split)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(transaction_id) DO UPDATE SET
                date=excluded.date,
                time=excluded.time,
                trans_type=excluded.trans_type,
                name=excluded.name,
                emoji=excluded.emoji,
                category=excluded.category,
                amount=excluded.amount,
                currency=excluded.currency,
                local_amount=excluded.local_amount,
                local_currency=excluded.local_currency,
                notes_and_tags=excluded.notes_and_tags,
                address=excluded.address,
                receipt=excluded.receipt,
                description=excluded.description,
                category_split=excluded.category_split,
                ingestion_timestamp=CURRENT_TIMESTAMP
            """, (self.transaction_id, self.date, self.time, self.trans_type, self.name, self.emoji, self.category, self.amount, self.currency, self.local_amount, self.local_currency, self.notes_and_tags, self.address, self.receipt, self.description, self.category_split))

    @classmethod
    def from_spreadsheet(cls, row):
        return cls(
        transaction_id=row['Transaction ID'],
        date=row['Date'],
        time=row['Time'],
        trans_type=row['Type'],
        name=row['Name'],
        emoji=row['Emoji'],
        category=row['Category'],
        amount=row['Amount'],
        currency=row['Currency'],
        local_amount=row['Local amount'],
        local_currency=row['Local currency'],
        notes_and_tags=row['Notes and #tags'],
        address=row['Address'],
        receipt=row['Receipt'],
        description=row['Description'],
        category_split=row['Category split']
    )
    


def pull_data():
    creds = ServiceAccountCredentials.from_json_keyfile_name("gsheet_creds.json", SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_KEY)
    worksheet = sheet.get_worksheet(1)
    return worksheet.get_all_records()


def main():
    data = pull_data()
    conn = get_db_connection(True)
    cursor = conn.cursor()

    MonzoRawTransaction.create_table(cursor)

    for row in data:
        trans = MonzoRawTransaction.from_spreadsheet(row)
        trans.insert(cursor)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
