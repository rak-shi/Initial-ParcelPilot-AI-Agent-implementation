from pathlib import Path


SOURCE_METADATA = {

    "01_Support_Policy_v3_CURRENT.pdf": {
        "source_type": "support_policy",
        "status": "CURRENT",
        "authority": 90,
        "scope": "GLOBAL",
        "authoritative": True,
        "description": (
            "Current global support policy"
        ),
    },

    "02_Support_Policy_v2_DEPRECATED.pdf": {
        "source_type": "support_policy",
        "status": "DEPRECATED",
        "authority": 0,
        "scope": "GLOBAL",
        "authoritative": False,
        "description": (
            "Deprecated historical policy"
        ),
    },

    "03_Cancellation_and_Service_Credit_SOP_v4.pdf": {
        "source_type": "sop",
        "status": "CURRENT",
        "authority": 90,
        "scope": "GLOBAL",
        "authoritative": True,
        "description": (
            "Current cancellation and service credit SOP"
        ),
    },

    "04_Product_Operations_Guide_and_Known_Issues.pdf": {
        "source_type": "product_documentation",
        "status": "CURRENT",
        "authority": 80,
        "scope": "GLOBAL",
        "authoritative": True,
        "description": (
            "Current product operations guide and known issues"
        ),
    },

    "05_Northstar_Logistics_Enterprise_Agreement.pdf": {
        "source_type": "customer_agreement",
        "status": "ACTIVE",
        "authority": 100,
        "scope": "ACCOUNT",
        "account_id": "ACCT-001",
        "authoritative": True,
        "description": (
            "Active Northstar Logistics agreement"
        ),
    },

    "06_LumenWorks_Service_Agreement.pdf": {
        "source_type": "customer_agreement",
        "status": "ACTIVE",
        "authority": 100,
        "scope": "ACCOUNT",
        "account_id": "ACCT-002",
        "authoritative": True,
        "description": (
            "Active LumenWorks agreement"
        ),
    },
}


def get_source_metadata(filename: str) -> dict:

    return SOURCE_METADATA.get(
        filename,
        {
            "source_type": "unknown",
            "status": "UNKNOWN",
            "authority": 0,
            "scope": "UNKNOWN",
            "authoritative": False,
            "description": "Unknown source",
        },
    )


def is_authoritative(metadata: dict) -> bool:

    return (
        metadata.get("authoritative", False)
        and metadata.get("status")
        not in ["DEPRECATED", "UNKNOWN"]
    )


def is_source_accessible(
    metadata: dict,
    user_context: dict,
) -> bool:
    """
    Enforces access to customer-specific agreements.

    A customer can access:
    - Global sources
    - Their own agreement

    They cannot access another customer's agreement.
    """

    scope = metadata.get("scope")

    if scope == "GLOBAL":
        return True

    if scope == "ACCOUNT":

        source_account_id = metadata.get(
            "account_id"
        )

        # Internal users can access authorised
        # operational sources.
        if user_context["role"] in [
            "support",
            "operations",
        ]:
            return True

        # Customer can only access own account.
        return (
            user_context.get("account_id")
            == source_account_id
        )

    return False


def get_precedence_rank(
    metadata: dict,
) -> int:
    """
    Source precedence:

    100 = Active customer agreement
     90 = Current policy / SOP
     80 = Current product documentation
     20 = Historical context
      0 = Deprecated / unknown
    """

    if metadata.get(
        "status"
    ) == "DEPRECATED":
        return 0

    return metadata.get(
        "authority",
        0,
    )


def sort_by_reliability(
    sources: list[dict],
) -> list[dict]:

    return sorted(
        sources,
        key=lambda source: get_precedence_rank(
            source.get(
                "metadata",
                source,
            )
        ),
        reverse=True,
    )