from backend.services.data_service import DataService
from backend.services.auth_service import get_user_context
from backend.services.snapshot_service import get_snapshot_time


def main():

    print("\n" + "=" * 70)
    print("PARCELPILOT STRUCTURED DATA TOOL TEST")
    print("=" * 70)

    # ==========================================
    # INITIALIZE SERVICES
    # ==========================================

    data_service = DataService()

    snapshot_time = get_snapshot_time()

    # ==========================================
    # LOAD USER CONTEXTS
    # ==========================================

    northstar_user = get_user_context(
        "northstar_customer"
    )

    lumen_user = get_user_context(
        "lumen_customer"
    )

    support_user = get_user_context(
        "support_agent"
    )

    # ==========================================
    # DEBUG USER CONTEXT
    # ==========================================

    print("\n" + "-" * 70)
    print("DEBUG USER CONTEXTS")
    print("-" * 70)

    print("\nNorthstar User:")
    print(northstar_user)

    print("\nLumenWorks User:")
    print(lumen_user)

    print("\nSupport User:")
    print(support_user)
    print("Support Role:", repr(support_user.get("role")))

    # ==========================================
    # TEST 1
    # NORTHSTAR ACCESSES OWN ORDER
    # ==========================================

    print("\n" + "=" * 70)
    print("TEST 1: NORTHSTAR -> ORD-1001")
    print("=" * 70)

    order = data_service.get_order_for_user(
        "ORD-1001",
        northstar_user,
    )

    print("\nResult:")
    print(order)

    if order:

        minutes = (
            data_service.get_cancellation_minutes(
                order
            )
        )

        print(
            "\nCancellation minutes:",
            minutes,
        )

    # ==========================================
    # TEST 2
    # NORTHSTAR TRIES TO ACCESS LUMEN ORDER
    # MUST BE DENIED
    # ==========================================

    print("\n" + "=" * 70)
    print(
        "TEST 2: NORTHSTAR -> ORD-2001 "
        "(MUST BE DENIED)"
    )
    print("=" * 70)

    order = data_service.get_order_for_user(
        "ORD-2001",
        northstar_user,
    )

    print("\nResult:")
    print(order)

    if order is None:

        print(
            "\nSUCCESS: Cross-account access denied."
        )

    else:

        print(
            "\nERROR: Cross-account access was allowed."
        )

    # ==========================================
    # TEST 3
    # INTERNAL SUPPORT ACCESSES LUMEN ORDER
    # MUST BE ALLOWED
    # ==========================================

    print("\n" + "=" * 70)
    print("TEST 3: INTERNAL SUPPORT -> ORD-2001")
    print("=" * 70)

    # Direct database lookup first
    print("\nDEBUG: Direct database lookup:")

    direct_order = data_service.get_order(
        "ORD-2001"
    )

    print(direct_order)

    # Access-controlled lookup
    print(
        "\nDEBUG: Access-controlled lookup:"
    )

    order = data_service.get_order_for_user(
        "ORD-2001",
        support_user,
    )

    print("\nFinal Result:")
    print(order)

    if order:

        print(
            "\nSUCCESS: Internal support access granted."
        )

        minutes = (
            data_service.get_cancellation_minutes(
                order
            )
        )

        print(
            "Cancellation minutes:",
            minutes,
        )

    else:

        print(
            "\nERROR: Internal support access denied."
        )

        print(
            "Check support_user role and "
            "get_order_for_user() logic."
        )

    # ==========================================
    # TEST 4
    # PICKUP DELAY USING DATASET SNAPSHOT TIME
    # ==========================================

    print("\n" + "=" * 70)
    print("TEST 4: PICKUP DELAY -> ORD-2002")
    print("=" * 70)

    print(
        "\nDataset Snapshot Time:",
        snapshot_time,
    )

    order = data_service.get_order_for_user(
        "ORD-2002",
        lumen_user,
    )

    print("\nOrder Result:")
    print(order)

    if order:

        delay = (
            data_service.get_pickup_delay_minutes(
                order,
                snapshot_time,
            )
        )

        print(
            "\nPickup delay minutes:",
            delay,
        )

        if delay == 270.0:

            print(
                "SUCCESS: Snapshot calculation is correct."
            )

        else:

            print(
                "WARNING: Expected approximately 270 minutes."
            )

    # ==========================================
    # TEST 5
    # LUMEN TRIES TO ACCESS NORTHSTAR TICKET
    # MUST BE DENIED
    # ==========================================

    print("\n" + "=" * 70)
    print(
        "TEST 5: LUMEN -> TKT-501 "
        "(MUST BE DENIED)"
    )
    print("=" * 70)

    ticket = data_service.get_ticket_for_user(
        "TKT-501",
        lumen_user,
    )

    print("\nResult:")
    print(ticket)

    if ticket is None:

        print(
            "\nSUCCESS: Cross-account ticket access denied."
        )

    else:

        print(
            "\nERROR: Cross-account ticket access was allowed."
        )

    # ==========================================
    # FINAL SUMMARY
    # ==========================================

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

    print(
        "\nSecurity and data tool tests completed."
    )


if __name__ == "__main__":
    main()