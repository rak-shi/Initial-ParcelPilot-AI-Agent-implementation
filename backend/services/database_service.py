import sqlite3

import pandas as pd

from backend.config import (
    EXCEL_FILE,
    SQLITE_DB_PATH,
)


ALLOWED_TABLES = {
    "accounts",
    "orders",
    "tickets",
    "escalations",
}


class DatabaseService:

    def __init__(self):

        self.db_path = str(SQLITE_DB_PATH)

    def get_connection(self):

        connection = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
        )

        connection.row_factory = sqlite3.Row

        return connection

    def load_workbook(self):

        if not EXCEL_FILE.exists():

            raise FileNotFoundError(
                f"Workbook not found: {EXCEL_FILE}"
            )

        excel = pd.ExcelFile(EXCEL_FILE)

        connection = self.get_connection()

        try:

            for sheet_name in [
                "accounts",
                "orders",
                "tickets",
            ]:

                dataframe = pd.read_excel(
                    EXCEL_FILE,
                    sheet_name=sheet_name,
                )

                # Convert all datetime columns to a
                # SQLite-friendly ISO format.
                for column in dataframe.columns:

                    if pd.api.types.is_datetime64_any_dtype(
                        dataframe[column]
                    ):

                        dataframe[column] = dataframe[
                            column
                        ].apply(
                            lambda value:
                            value.isoformat()
                            if pd.notna(value)
                            else None
                        )

                dataframe.to_sql(
                    sheet_name,
                    connection,
                    if_exists="replace",
                    index=False,
                )

                print(
                    f"Loaded {sheet_name}: "
                    f"{len(dataframe)} rows"
                )

            self.create_escalations_table(
                connection
            )

            connection.commit()

        finally:

            connection.close()

    def create_escalations_table(
        self,
        connection,
    ):

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS escalations (
                escalation_id TEXT PRIMARY KEY,
                account_id TEXT,
                ticket_id TEXT,
                order_id TEXT,
                reason TEXT NOT NULL,
                priority TEXT NOT NULL,
                created_by TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

    def get_table_columns(
        self,
        table_name: str,
    ):

        if table_name not in ALLOWED_TABLES:

            raise ValueError(
                f"Table not allowed: {table_name}"
            )

        connection = self.get_connection()

        try:

            rows = connection.execute(
                f"PRAGMA table_info({table_name})"
            ).fetchall()

            return [
                row["name"]
                for row in rows
            ]

        finally:

            connection.close()