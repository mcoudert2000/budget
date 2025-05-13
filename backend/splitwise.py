import sqlite3
import requests
import os
import json
from typing import Optional, List

from app import get_db_connection

BASE_URL = "https://secure.splitwise.com/api/v3.0/"

class SplitwiseApi():
    def __init__(self):
        self.api_key = os.environ['SPLITWISE_API_KEY']
        self.consumer_key = os.environ['SPLITWISE_CONSUMER_KEY']
        self.consumer_secret = os.environ['SPLITWISE_CONSUMER_SECRET']

    def make_request(self, method, params):
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        response = requests.post(BASE_URL + method, headers=headers, params=params)
        return response.json()

    def get_expenses(self, limit: int = 50, offset: int = 0):
        return self.make_request('get_expenses', {
            'limit': limit,
            'offset': offset
        })


class SplitwiseRawTransaction:
    def __init__(self,
                 id: int,
                 group_id: Optional[int],
                 expense_bundle_id: Optional[int],
                 description: str,
                 repeats: bool,
                 repeat_interval: Optional[str],
                 email_reminder: bool,
                 email_reminder_in_advance: int,
                 next_repeat: Optional[str],
                 details: Optional[str],
                 comments_count: int,
                 payment: bool,
                 creation_method: str,
                 transaction_method: str,
                 transaction_confirmed: bool,
                 transaction_id: Optional[int],
                 transaction_status: Optional[str],
                 cost: str,
                 currency_code: str,
                 date: str,
                 created_at: str,
                 updated_at: Optional[str],
                 deleted_at: Optional[str],
                 created_by: Optional[str],
                 updated_by: Optional[str],
                 deleted_by: Optional[str],
                 category: Optional[str],
                 receipt: Optional[str],
                 repayments: List[dict],
                 users: List[dict]):
        self.id = id
        self.group_id = group_id
        self.expense_bundle_id = expense_bundle_id
        self.description = description
        self.repeats = repeats
        self.repeat_interval = repeat_interval
        self.email_reminder = email_reminder
        self.email_reminder_in_advance = email_reminder_in_advance
        self.next_repeat = next_repeat
        self.details = details
        self.comments_count = comments_count
        self.payment = payment
        self.creation_method = creation_method
        self.transaction_method = transaction_method
        self.transaction_confirmed = transaction_confirmed
        self.transaction_id = transaction_id
        self.transaction_status = transaction_status
        self.cost = cost
        self.currency_code = currency_code
        self.date = date
        self.created_at = created_at
        self.updated_at = updated_at
        self.deleted_at = deleted_at
        self.created_by = created_by
        self.updated_by = updated_by
        self.deleted_by = deleted_by
        self.category = category
        self.receipt = receipt
        self.repayments = repayments
        self.users = users

    @classmethod
    def from_api(cls, data: dict):
        """
        Factory method to create an instance of SplitwiseRawTransaction from API data (dict).
        """
        return cls(
            id=data.get("id"),
            group_id=data.get("group_id"),
            expense_bundle_id=data.get("expense_bundle_id"),
            description=data.get("description"),
            repeats=data.get("repeats"),
            repeat_interval=data.get("repeat_interval"),
            email_reminder=data.get("email_reminder"),
            email_reminder_in_advance=data.get("email_reminder_in_advance"),
            next_repeat=data.get("next_repeat"),
            details=data.get("details"),
            comments_count=data.get("comments_count"),
            payment=data.get("payment"),
            creation_method=data.get("creation_method"),
            transaction_method=data.get("transaction_method"),
            transaction_confirmed=data.get("transaction_confirmed"),
            transaction_id=data.get("transaction_id"),
            transaction_status=data.get("transaction_status"),
            cost=data.get("cost"),
            currency_code=data.get("currency_code"),
            date=data.get("date"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            deleted_at=data.get("deleted_at"),
            created_by=str(data.get("created_by")),
            updated_by=str(data.get("updated_by")),
            deleted_by=str(data.get("deleted_by")),
            category=str(data.get("category")),
            receipt=str(data.get("receipt")),
            repayments=data.get("repayments", []),  # Repayments list
            users=data.get("users", [])  # Users list
        )

    def insert_into_db(self, cursor: sqlite3.Cursor):
        """
        Insert the SplitwiseRawTransaction data into an SQLite database.
        """
        cursor.execute("""
            INSERT INTO splitwise_raw (
                id, group_id, expense_bundle_id, description, repeats, repeat_interval, 
                email_reminder, email_reminder_in_advance, next_repeat, details, 
                comments_count, payment, creation_method, transaction_method, transaction_confirmed, 
                transaction_id, transaction_status, cost, currency_code, date, created_at, 
                updated_at, deleted_at, created_by, updated_by, deleted_by, category, receipt, 
                repayments, users, ingestion_timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
            group_id = excluded.group_id,
            expense_bundle_id = excluded.expense_bundle_id,
            description = excluded.description,
            repeats = excluded.repeats,
            repeat_interval = excluded.repeat_interval,
            email_reminder = excluded.email_reminder,
            email_reminder_in_advance = excluded.email_reminder_in_advance,
            next_repeat = excluded.next_repeat,
            details = excluded.details,
            comments_count = excluded.comments_count,
            payment = excluded.payment,
            creation_method = excluded.creation_method,
            transaction_method = excluded.transaction_method,
            transaction_confirmed = excluded.transaction_confirmed,
            transaction_id = excluded.transaction_id,
            transaction_status = excluded.transaction_status,
            cost = excluded.cost,
            currency_code = excluded.currency_code,
            date = excluded.date,
            created_at = excluded.created_at,
            updated_at = excluded.updated_at,
            deleted_at = excluded.deleted_at,
            created_by = excluded.created_by,
            updated_by = excluded.updated_by,
            deleted_by = excluded.deleted_by,
            category = excluded.category,
            receipt = excluded.receipt,
            repayments = excluded.repayments,
            users = excluded.users,
            ingestion_timestamp=CURRENT_TIMESTAMP
        """, (
            self.id, self.group_id, self.expense_bundle_id, self.description, self.repeats,
            self.repeat_interval, self.email_reminder, self.email_reminder_in_advance,
            self.next_repeat, self.details, self.comments_count, self.payment,
            self.creation_method, self.transaction_method, self.transaction_confirmed,
            self.transaction_id, self.transaction_status, self.cost, self.currency_code,
            self.date, self.created_at, self.updated_at, self.deleted_at,
            self.created_by, self.updated_by, self.deleted_by,
            self.category, self.receipt,
            json.dumps(self.repayments),
            json.dumps(self.users)
        ))

    @staticmethod
    def create_table(cursor: sqlite3.Cursor):
        """
        Creates the splitwise_raw table in the SQLite database.
        """
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS splitwise_raw (
                id INTEGER PRIMARY KEY,
                group_id INTEGER,
                expense_bundle_id INTEGER,
                description TEXT,
                repeats BOOLEAN,
                repeat_interval TEXT,
                email_reminder BOOLEAN,
                email_reminder_in_advance INTEGER,
                next_repeat TEXT,
                details TEXT,
                comments_count INTEGER,
                payment BOOLEAN,
                creation_method TEXT,
                transaction_method TEXT,
                transaction_confirmed BOOLEAN,
                transaction_id INTEGER,
                transaction_status TEXT,
                cost TEXT,
                currency_code TEXT,
                date TEXT,
                created_at TEXT,
                updated_at TEXT,
                deleted_at TEXT,
                created_by TEXT,
                updated_by TEXT,
                deleted_by TEXT,
                category TEXT,
                receipt TEXT,
                repayments TEXT,
                users TEXT,
                ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)



def main():
    splitwise = SplitwiseApi()
    expenses = splitwise.get_expenses(2000)
    conn = get_db_connection(True)
    cursor = conn.cursor()

    SplitwiseRawTransaction.create_table(cursor)

    [SplitwiseRawTransaction.from_api(expense).insert_into_db(cursor) for expense in expenses['expenses']]
    conn.commit()


if __name__ == '__main__':
    main()


