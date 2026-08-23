from backend.services.action_service import ActionService
from backend.services.auth_service import get_user_context


def print_section(title):
    print("\n" + "=" * 76)
    print(title)
    print("=" * 76)


def main():
    print("\nPARCELPILOT STATE-CHANGING ACTION TOOL TEST")

    action_service = ActionService()

    # ============================================================
    # USER CONTEXTS
    # ============================================================

    northstar_user = get_user_context("northstar_customer")
    lumen_user = get_user_context("lumen_customer")
    support_user = get_user_context("support_agent")

    print_section("DEBUG USER CONTEXTS")

    print("\nNorthstar User:")
    print(northstar_user)

    print("\nLumenWorks User:")
    print(lumen_user)

    print("\nSupport User:")
    print(support_user)

    # ============================================================
    # TEST 1: PREPARE ESCALATION
    # IMPORTANT: This must NOT execute the action.
    # ============================================================

    print_section(
        "TEST 1: PREPARE ESCALATION - MUST REQUIRE CONFIRMATION"
    )

    prepare_result = action_service.prepare_escalation(
        user_context=northstar_user,
        account_id="ACCT-001",
        title="Cancellation request requires support review",
        reason=(
            "Customer requested escalation for cancellation of "
            "ORD-1001."
        ),
        priority="P2",
        related_order_id="ORD-1001",
        details=(
            "Customer wants the cancellation request reviewed "
            "by the support team."
        ),
    )

    print("\nPrepare Result:")
    print(prepare_result)

    if not prepare_result.get("success"):
        print("\nFAILED: Could not prepare escalation.")
        return

    if prepare_result.get("executed") is True:
        print(
            "\nFAILED: Action was executed without confirmation!"
        )
        return

    if prepare_result.get("confirmation_required") is not True:
        print(
            "\nFAILED: Confirmation was not required!"
        )
        return

    print(
        "\nSUCCESS: Escalation prepared but NOT executed."
    )

    action = prepare_result["action"]
    action_id = action["action_id"]

    print(f"\nPending Action ID: {action_id}")

    # ============================================================
    # TEST 2: VERIFY PENDING ACTION EXISTS
    # ============================================================

    print_section(
        "TEST 2: VERIFY PENDING ACTION EXISTS"
    )

    pending_action = action_service.get_pending_action(
        action_id=action_id,
        user_context=northstar_user,
    )

    print("\nPending Action:")
    print(pending_action)

    if pending_action is None:
        print(
            "\nFAILED: Pending action could not be found."
        )
        return

    if pending_action.get("status") != "PENDING_CONFIRMATION":
        print(
            "\nFAILED: Action is not in PENDING_CONFIRMATION state."
        )
        return

    print(
        "\nSUCCESS: Action is pending confirmation."
    )

    # ============================================================
    # TEST 3: CROSS-ACCOUNT ACCESS MUST BE DENIED
    # LumenWorks must not access Northstar's action.
    # ============================================================

    print_section(
        "TEST 3: LUMENWORKS ACCESSING NORTHSTAR ACTION - MUST BE DENIED"
    )

    unauthorized_action = action_service.get_pending_action(
        action_id=action_id,
        user_context=lumen_user,
    )

    print("\nResult:")
    print(unauthorized_action)

    if unauthorized_action is None:
        print(
            "\nSUCCESS: Cross-account action access denied."
        )
    else:
        print(
            "\nFAILED: Cross-account action access was allowed!"
        )
        return

    # ============================================================
    # TEST 4: UNAUTHORISED USER CANNOT CONFIRM
    # ============================================================

    print_section(
        "TEST 4: LUMENWORKS CONFIRMING NORTHSTAR ACTION - MUST BE DENIED"
    )

    unauthorized_confirm = action_service.confirm_action(
        action_id=action_id,
        user_context=lumen_user,
        confirmed=True,
    )

    print("\nResult:")
    print(unauthorized_confirm)

    if unauthorized_confirm.get("success") is False:
        print(
            "\nSUCCESS: Unauthorised confirmation denied."
        )
    else:
        print(
            "\nFAILED: Unauthorised user confirmed the action!"
        )
        return

    # ============================================================
    # TEST 5: OWNER EXPLICITLY CONFIRMS ACTION
    # This is where the state-changing action actually happens.
    # ============================================================

    print_section(
        "TEST 5: NORTHSTAR EXPLICITLY CONFIRMS ESCALATION"
    )

    confirm_result = action_service.confirm_action(
        action_id=action_id,
        user_context=northstar_user,
        confirmed=True,
    )

    print("\nConfirmation Result:")
    print(confirm_result)

    if not confirm_result.get("success"):
        print(
            "\nFAILED: Confirmation failed."
        )
        return

    if confirm_result.get("executed") is not True:
        print(
            "\nFAILED: Action was not executed after confirmation."
        )
        return

    confirmed_action = confirm_result["action"]

    if confirmed_action.get("status") != "EXECUTED":
        print(
            "\nFAILED: Action status is not EXECUTED."
        )
        return

    print(
        "\nSUCCESS: Escalation executed ONLY after explicit confirmation."
    )

    # ============================================================
    # TEST 6: ACTION SHOULD NO LONGER BE PENDING
    # ============================================================

    print_section(
        "TEST 6: VERIFY ACTION IS NO LONGER PENDING"
    )

    pending_after_confirmation = action_service.get_pending_action(
        action_id=action_id,
        user_context=northstar_user,
    )

    print("\nPending Lookup Result:")
    print(pending_after_confirmation)

    if pending_after_confirmation is None:
        print(
            "\nSUCCESS: Executed action removed from pending actions."
        )
    else:
        print(
            "\nFAILED: Executed action still exists as pending!"
        )
        return

    # ============================================================
    # TEST 7: VERIFY EXECUTED ACTION EXISTS
    # ============================================================

    print_section(
        "TEST 7: VERIFY EXECUTED ACTION EXISTS"
    )

    executed_actions = action_service.get_executed_actions(
        user_context=northstar_user,
    )

    print("\nNorthstar Executed Actions:")

    for item in executed_actions:
        print(item)

    matching_actions = [
        item
        for item in executed_actions
        if item.get("action_id") == action_id
    ]

    if matching_actions:
        print(
            "\nSUCCESS: Confirmed escalation exists in executed actions."
        )
    else:
        print(
            "\nFAILED: Executed escalation was not found."
        )
        return

    # ============================================================
    # TEST 8: CUSTOMER CANNOT SEE ANOTHER ACCOUNT'S ACTIONS
    # ============================================================

    print_section(
        "TEST 8: LUMENWORKS CANNOT SEE NORTHSTAR EXECUTED ACTION"
    )

    lumen_actions = action_service.get_executed_actions(
        user_context=lumen_user,
    )

    print("\nLumenWorks Executed Actions:")

    for item in lumen_actions:
        print(item)

    leaked_actions = [
        item
        for item in lumen_actions
        if item.get("action_id") == action_id
    ]

    if not leaked_actions:
        print(
            "\nSUCCESS: Cross-account executed action data is protected."
        )
    else:
        print(
            "\nFAILED: Northstar action leaked to LumenWorks!"
        )
        return

    # ============================================================
    # FINAL RESULT
    # ============================================================

    print_section("ALL ACTION SERVICE TESTS COMPLETED")

    print(
        "\nSUCCESS: State-changing action workflow works correctly."
    )

    print(
        "\nVerified requirements:"
    )

    print(
        "1. Action can be prepared without execution."
    )

    print(
        "2. Explicit confirmation is required."
    )

    print(
        "3. Cross-account access is denied."
    )

    print(
        "4. Unauthorised users cannot confirm actions."
    )

    print(
        "5. Action executes only after confirmation."
    )

    print(
        "6. Executed actions are stored separately."
    )

    print(
        "7. Customer data remains account-scoped."
    )


if __name__ == "__main__":
    main()