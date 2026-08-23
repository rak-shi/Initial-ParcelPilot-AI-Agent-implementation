# backend/services/auth_service.py


MOCK_USERS = {
    "northstar_customer": {
        "username": "northstar_customer",
        "display_name": "Northstar Logistics Customer",
        "role": "customer",
        "account_id": "ACCT-001",
    },
    "lumen_customer": {
        "username": "lumen_customer",
        "display_name": "LumenWorks Customer",
        "role": "customer",
        "account_id": "ACCT-002",
    },
    "beacon_customer": {
        "username": "beacon_customer",
        "display_name": "Beacon Retail Customer",
        "role": "customer",
        "account_id": "ACCT-003",
    },
    "axis_customer": {
        "username": "axis_customer",
        "display_name": "Axis Labs Customer",
        "role": "customer",
        "account_id": "ACCT-004",
    },
    "support_agent": {
        "username": "support_agent",
        "display_name": "ParcelPilot Support Agent",
        "role": "support",
        "account_id": None,
    },
    "support_manager": {
        "username": "support_manager",
        "display_name": "ParcelPilot Support Manager",
        "role": "support_manager",
        "account_id": None,
    },
}


def get_user_context(username: str) -> dict | None:
    """
    Returns the mock authenticated user's context.

    In production, this would come from a real authentication
    and authorization system.
    """

    return MOCK_USERS.get(username)


def get_all_users() -> list[dict]:
    """
    Returns available mock users.
    Useful for the demo interface.
    """

    return list(MOCK_USERS.values())


def is_customer(user_context: dict) -> bool:
    """
    Checks whether the user is a customer.
    """

    return user_context.get("role") == "customer"


def is_internal_user(user_context: dict) -> bool:
    """
    Checks whether the user is an authorized ParcelPilot employee.
    """

    internal_roles = {
        "support",
        "support_agent",
        "support_manager",
        "operations",
        "admin",
    }

    return user_context.get("role") in internal_roles