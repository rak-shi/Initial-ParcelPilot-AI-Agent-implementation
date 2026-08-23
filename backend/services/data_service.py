import sqlite3
from datetime import datetime

from backend.config import SQLITE_DB_PATH


class DataService:

    # ============================================================
    # DATABASE CONNECTION
    # ============================================================

    def get_connection(self):
        connection = sqlite3.connect(SQLITE_DB_PATH)
        connection.row_factory = sqlite3.Row
        return connection

    # ============================================================
    # ACCOUNT LOOKUP
    # ============================================================

    def get_account(self, account_id: str) -> dict | None:
        connection = self.get_connection()

        try:
            cursor = connection.execute(
                """
                SELECT *
                FROM accounts
                WHERE account_id = ?
                """,
                (account_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return dict(row)

        finally:
            connection.close()

    # ============================================================
    # FIND ACCOUNT BY NAME
    # ============================================================

    def find_account_by_name(
        self,
        account_name: str,
    ) -> dict | None:

        connection = self.get_connection()

        try:
            cursor = connection.execute(
                """
                SELECT *
                FROM accounts
                WHERE LOWER(account_name) LIKE LOWER(?)
                """,
                (f"%{account_name.strip()}%",),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return dict(row)

        finally:
            connection.close()

    # ============================================================
    # ORDER LOOKUP
    # ============================================================

    def get_order(self, order_id: str) -> dict | None:
        connection = self.get_connection()

        try:
            cursor = connection.execute(
                """
                SELECT *
                FROM orders
                WHERE order_id = ?
                """,
                (order_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return dict(row)

        finally:
            connection.close()

    # ============================================================
    # GET ACCOUNT ORDERS
    # ============================================================

    def get_account_orders(
        self,
        account_id: str,
    ) -> list[dict]:

        connection = self.get_connection()

        try:
            cursor = connection.execute(
                """
                SELECT *
                FROM orders
                WHERE account_id = ?
                ORDER BY booked_at DESC
                """,
                (account_id,),
            )

            rows = cursor.fetchall()

            return [
                dict(row)
                for row in rows
            ]

        finally:
            connection.close()

    # ============================================================
    # TICKET LOOKUP
    # ============================================================

    def get_ticket(self, ticket_id: str) -> dict | None:
        connection = self.get_connection()

        try:
            cursor = connection.execute(
                """
                SELECT *
                FROM tickets
                WHERE ticket_id = ?
                """,
                (ticket_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return dict(row)

        finally:
            connection.close()

    # ============================================================
    # GET ACCOUNT TICKETS
    # ============================================================

    def get_account_tickets(
        self,
        account_id: str,
    ) -> list[dict]:

        connection = self.get_connection()

        try:
            cursor = connection.execute(
                """
                SELECT *
                FROM tickets
                WHERE account_id = ?
                ORDER BY created_at DESC
                """,
                (account_id,),
            )

            rows = cursor.fetchall()

            return [
                dict(row)
                for row in rows
            ]

        finally:
            connection.close()

    # ============================================================
    # GET OPEN TICKETS
    # ============================================================

    def get_open_tickets(
        self,
        account_id: str | None = None,
    ) -> list[dict]:

        connection = self.get_connection()

        try:

            if account_id:

                cursor = connection.execute(
                    """
                    SELECT *
                    FROM tickets
                    WHERE status = 'open'
                    AND account_id = ?
                    ORDER BY created_at ASC
                    """,
                    (account_id,),
                )

            else:

                cursor = connection.execute(
                    """
                    SELECT *
                    FROM tickets
                    WHERE status = 'open'
                    ORDER BY created_at ASC
                    """
                )

            rows = cursor.fetchall()

            return [
                dict(row)
                for row in rows
            ]

        finally:
            connection.close()

    # ============================================================
    # CANCELLATION TIME CALCULATION
    # ============================================================

    def get_cancellation_minutes(
        self,
        order: dict,
    ) -> float | None:

        if not order or not isinstance(order, dict):
            return None

        booked_at = order.get("booked_at")

        cancellation_requested_at = order.get(
            "cancellation_requested_at"
        )

        if not booked_at or not cancellation_requested_at:
            return None

        try:

            booked_time = datetime.fromisoformat(
                str(booked_at)
            )

            cancellation_time = datetime.fromisoformat(
                str(cancellation_requested_at)
            )

            difference = (
                cancellation_time - booked_time
            )

            return round(
                difference.total_seconds() / 60,
                2,
            )

        except (TypeError, ValueError):
            return None

    # ============================================================
    # PICKUP DELAY CALCULATION
    # ============================================================

    def get_pickup_delay_minutes(
        self,
        order: dict,
        reference_time,
    ) -> float | None:
        """
        Calculate pickup delay.

        IMPORTANT:
        order must be the complete order dictionary.

        Correct:
            get_pickup_delay_minutes(order, snapshot_time)

        Wrong:
            get_pickup_delay_minutes(order_id, snapshot_time)
        """

        if not order or not isinstance(order, dict):
            return None

        pickup_window_end = order.get(
            "pickup_window_end"
        )

        if not pickup_window_end:
            return None

        try:

            window_end = datetime.fromisoformat(
                str(pickup_window_end)
            )

        except (TypeError, ValueError):
            return None

        pickup_actual_at = order.get(
            "pickup_actual_at"
        )

        # --------------------------------------------------------
        # ACTUAL PICKUP EXISTS
        # --------------------------------------------------------

        if pickup_actual_at:

            try:

                actual_time = datetime.fromisoformat(
                    str(pickup_actual_at)
                )

                difference = actual_time - window_end

                return round(
                    max(
                        0,
                        difference.total_seconds() / 60,
                    ),
                    2,
                )

            except (TypeError, ValueError):
                return None

        # --------------------------------------------------------
        # NO ACTUAL PICKUP
        # USE DATASET SNAPSHOT TIME
        # --------------------------------------------------------

        snapshot = reference_time

        if snapshot is None:
            return None

        # pandas Timestamp / datetime may be timezone-aware.
        # Workbook timestamps are naive, so remove timezone.
        if getattr(snapshot, "tzinfo", None) is not None:

            snapshot = snapshot.replace(
                tzinfo=None
            )

        try:

            difference = snapshot - window_end

            return round(
                max(
                    0,
                    difference.total_seconds() / 60,
                ),
                2,
            )

        except (TypeError, ValueError):
            return None

    # ============================================================
    # INTERNAL ROLE CHECK
    # ============================================================

    def is_internal_user(
        self,
        user_context: dict,
    ) -> bool:

        if not user_context:
            return False

        internal_roles = {
            "support",
            "support_agent",
            "support_manager",
            "operations",
            "admin",
            "manager",
            "internal",
        }

        role = str(
            user_context.get("role", "")
        ).lower()

        return role in internal_roles

    # ============================================================
    # ACCESS-CONTROLLED ACCOUNT LOOKUP
    # ============================================================

    def get_account_for_user(
        self,
        account_id: str,
        user_context: dict,
    ) -> dict | None:

        if not user_context:
            return None

        # Internal users can access all accounts.
        if self.is_internal_user(user_context):
            return self.get_account(account_id)

        # Customers can access only their own account.
        if (
            user_context.get("role") == "customer"
            and user_context.get("account_id") == account_id
        ):
            return self.get_account(account_id)

        return None

    # ============================================================
    # ACCESS-CONTROLLED ORDER LOOKUP
    # ============================================================

    def get_order_for_user(
        self,
        order_id: str,
        user_context: dict,
    ) -> dict | None:

        if not user_context:
            return None

        order = self.get_order(order_id)

        if order is None:
            return None

        # Internal users can access all orders.
        if self.is_internal_user(user_context):
            return order

        # Customers can access only their own account orders.
        if (
            user_context.get("role") == "customer"
            and order.get("account_id")
            == user_context.get("account_id")
        ):
            return order

        # Cross-account access denied.
        return None

    # ============================================================
    # ACCESS-CONTROLLED TICKET LOOKUP
    # ============================================================

    def get_ticket_for_user(
        self,
        ticket_id: str,
        user_context: dict,
    ) -> dict | None:

        if not user_context:
            return None

        ticket = self.get_ticket(ticket_id)

        if ticket is None:
            return None

        # Internal users can access all tickets.
        if self.is_internal_user(user_context):
            return ticket

        # Customers can access only their own account tickets.
        if (
            user_context.get("role") == "customer"
            and ticket.get("account_id")
            == user_context.get("account_id")
        ):
            return ticket

        # Cross-account access denied.
        return None