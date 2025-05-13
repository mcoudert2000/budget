import tkinter as tk
from tkinter import filedialog
import pandas as pd
import sqlite3
from typing import Optional

from app import get_db_connection


def select_and_parse_amex_file():
    root = tk.Tk()
    root.withdraw()

    return filedialog.askopenfilename(title="Select CSV files", filetypes=[("CSV files", "*.csv")])


class AmexRawTransaction:
    def __init__(self,
                 date: str,
                 description: str,
                 amount: float,
                 extended_details: Optional[str],
                 appears_on_statement_as: Optional[str],
                 address: Optional[str],
                 town_city: Optional[str],
                 postcode: Optional[str],
                 country: Optional[str],
                 reference: str,  # Primary key
                 category: Optional[str]):
        self.date = date
        self.description = description
        self.amount = amount
        self.extended_details = extended_details
        self.appears_on_statement_as = appears_on_statement_as
        self.address = address
        self.town_city = town_city
        self.postcode = postcode
        self.country = country
        self.reference = reference
        self.category = category

    @classmethod
    def from_dataframe(cls, row: pd.Series):
        """
        Factory method to create an AmexTransactionRaw instance from a single row of a pandas DataFrame.
        """
        return cls(
            date=row.get("Date"),
            description=row.get("Description"),
            amount=row.get("Amount"),
            extended_details=row.get("Extended Details"),
            appears_on_statement_as=row.get("Appears On Your Statement As"),
            address=row.get("Address"),
            town_city=row.get("Town/City"),
            postcode=row.get("Postcode"),
            country=row.get("Country"),
            reference=row.get("Reference"),  # Primary key
            category=row.get("Category")
        )

    def insert_into_db(self, cursor: sqlite3.Cursor):
        """
        Insert the AmexTransactionRaw data into an SQLite database.
        On conflict of reference (primary key), update all other columns.
        """
        cursor.execute("""
            INSERT INTO amex_raw (
                date, description, amount, extended_details, appears_on_statement_as, 
                address, town_city, postcode, country, reference, category, ingestion_timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(reference) DO UPDATE SET
                date = excluded.date,
                description = excluded.description,
                amount = excluded.amount,
                extended_details = excluded.extended_details,
                appears_on_statement_as = excluded.appears_on_statement_as,
                address = excluded.address,
                town_city = excluded.town_city,
                postcode = excluded.postcode,
                country = excluded.country,
                category = excluded.category,
                ingestion_timestamp = CURRENT_TIMESTAMP
        """, (
            self.date, self.description, self.amount, self.extended_details,
            self.appears_on_statement_as, self.address, self.town_city,
            self.postcode, self.country, self.reference, self.category
        ))

    @staticmethod
    def create_table(cursor: sqlite3.Cursor):
        """
        Creates the amex_raw table in the SQLite database.
        """
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS amex_raw (
                date TEXT,
                description TEXT,
                amount REAL,
                extended_details TEXT,
                appears_on_statement_as TEXT,
                address TEXT,
                town_city TEXT,
                postcode TEXT,
                country TEXT,
                reference TEXT PRIMARY KEY,
                category TEXT,
                ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def main():
    df = pd.read_csv(select_and_parse_amex_file())
    conn = get_db_connection(True)
    cursor = conn.cursor()
    AmexRawTransaction.create_table(cursor)

    for _, row in df.iterrows():
        transaction = AmexRawTransaction.from_dataframe(row)
        transaction.insert_into_db(cursor)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    main()