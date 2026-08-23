from backend.services.database_service import (
    DatabaseService,
)

from backend.services.auth_service import (
    require_account_access,
)


class DataTools:

    def __init__(self):

        self.database = DatabaseService()

    # ---------------------------------
    # ACCOUNT LOOKUP
    # ---------------------------------

    def get_account(
        self,
        account_id: str,
        user_context: dict,
    ) -> dict | None:

        require_account_access(
            user_context,
            account_id,
        )

        connection = (
            self.database.get_connection()
        )

        try:

            row = connection.execute(
                """
                SELECT
                    account_id,
                    account_name,
                    plan,
                    status,
                    csm,
                    contract_file,
                    premium_support,
                    notes
                FROM accounts
                WHERE account_id = ?
                """,
                (account_id,),
            ).fetchone()

            return (
                dict(row)
                if row
                else None
            )

        finally:

            connection.close()

    # ---------------------------------
    # ORDER LOOKUP
    # ---------------------------------

    def get_order(
        self,
        order_id: str,
        user_context: dict,
    ) -> dict | None:

        connection = (
            self.database.get_connection()
        )

        try:

            row = connection.execute(
                """
                SELECT *
                FROM orders
                WHERE order_id = ?
                """,
                (order_id,),
            ).fetchone()

            if row is None:
                return None

            order = dict(row)

            # Access is enforced here,
            # after determining the actual
            # account owner of the order.
            require_account_access(
                user_context,
                order["account_id"],
            )

            return order

        finally:

            connection.close()

    # ---------------------------------
    # TICKET LOOKUP
    # ---------------------------------

    def get_ticket(
        self,
        ticket_id: str,
        user_context: dict,
    ) -> dict | None:

        connection = (
            self.database.get_connection()
        )

        try:

            row = connection.execute(
                """
                SELECT *
                FROM tickets
                WHERE ticket_id = ?
                """,
                (ticket_id,),
            ).fetchone()

            if row is None:
                return None

            ticket = dict(row)

            require_account_access(
                user_context,
                ticket["account_id"],
            )

            return ticket

        finally:

            connection.close()

    # ---------------------------------
    # ACCOUNT TICKETS
    # ---------------------------------

    def get_account_tickets(
        self,
        account_id: str,
        user_context: dict,
    ) -> list[dict]:

        require_account_access(
            user_context,
            account_id,
        )

        connection = (
            self.database.get_connection()
        )

        try:

            rows = connection.execute(
                """
                SELECT *
                FROM tickets
                WHERE account_id = ?
                ORDER BY created_at DESC
                """,
                (account_id,),
            ).fetchall()

            return [
                dict(row)
                for row in rows
            ]

        finally:

            connection.close()

    # ---------------------------------
    # INTERNAL: ALL OPEN TICKETS
    # ---------------------------------

    def get_all_open_tickets(
        self,
        user_context: dict,
    ) -> list[dict]:

        if user_context["role"] not in [
            "support",
            "operations",
        ]:

            raise PermissionError(
                "Only authorised internal users "
                "can access all support tickets."
            )

        connection = (
            self.database.get_connection()
        )

        try:

            rows = connection.execute(
                """
                SELECT
                    t.*,
                    a.account_name,
                    a.plan,
                    a.premium_support
                FROM tickets t
                JOIN accounts a
                    ON t.account_id = a.account_id
                WHERE LOWER(t.status) = 'open'
                ORDER BY t.created_at ASC
                """
            ).fetchall()

            return [
                dict(row)
                for row in rows
            ]

        finally:

            connection.close()

    # ---------------------------------
    # INTERNAL: ALL ORDERS
    # ---------------------------------

    def get_all_orders(
        self,
        user_context: dict,
    ) -> list[dict]:

        if user_context["role"] not in [
            "support",
            "operations",
        ]:

            raise PermissionError(
                "Only authorised internal users "
                "can access all orders."
            )

        connection = (
            self.database.get_connection()
        )

        try:

            rows = connection.execute(
                """
                SELECT *
                FROM orders
                """
            ).fetchall()

            return [
                dict(row)
                for row in rows
            ]

        finally:

            connection.close()