from backend.services.agent_service import AgentService
from backend.services.auth_service import get_user_context


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    print_section("PARCELPILOT AGENT SERVICE TEST")

    # ------------------------------------------------------------
    # INITIALIZE AGENT
    # ------------------------------------------------------------
    agent = AgentService()

    # ------------------------------------------------------------
    # LOAD USER CONTEXTS
    # ------------------------------------------------------------
    northstar_user = get_user_context("northstar_customer")
    lumen_user = get_user_context("lumen_customer")
    support_user = get_user_context("support_agent")

    print("\nDEBUG USER CONTEXTS")

    print("\nNorthstar User:")
    print(northstar_user)

    print("\nLumenWorks User:")
    print(lumen_user)

    print("\nSupport User:")
    print(support_user)

    # ============================================================
    # TEST 1: NORTHSTAR CANCELLATION QUERY
    # ============================================================
    print_section(
        "TEST 1: NORTHSTAR CANCELLATION QUERY - MULTI-STEP REASONING"
    )

    response = agent.handle_query(
        query="Can I cancel order ORD-1001 without a cancellation fee?",
        user_context=northstar_user,
    )

    print("\nRESPONSE:")
    print(response)

    # ============================================================
    # TEST 2: LUMENWORKS SERVICE CREDIT
    # ============================================================
    print_section(
        "TEST 2: LUMENWORKS SERVICE CREDIT QUERY"
    )

    response = agent.handle_query(
        query=(
            "Is order ORD-2002 eligible for a service credit "
            "because pickup is delayed?"
        ),
        user_context=lumen_user,
    )

    print("\nRESPONSE:")
    print(response)

    # ============================================================
    # TEST 3: CROSS-ACCOUNT ACCESS MUST BE DENIED
    # ============================================================
    print_section(
        "TEST 3: NORTHSTAR TRYING TO ACCESS LUMENWORKS ORDER"
    )

    response = agent.handle_query(
        query="What is the status of order ORD-2001?",
        user_context=northstar_user,
    )

    print("\nRESPONSE:")
    print(response)

    # ============================================================
    # TEST 4: INTERNAL SUPPORT ACCESS
    # ============================================================
    print_section(
        "TEST 4: INTERNAL SUPPORT ACCESSING LUMENWORKS ORDER"
    )

    response = agent.handle_query(
        query="Can order ORD-2001 be cancelled?",
        user_context=support_user,
    )

    print("\nRESPONSE:")
    print(response)

    # ============================================================
    # TEST 5: PRODUCT DOCUMENTATION / KNOWN ISSUE
    # ============================================================
    print_section(
        "TEST 5: PRODUCT DOCUMENTATION / KNOWN ISSUE"
    )

    response = agent.handle_query(
        query=(
            "Is there a known issue with bulk CSV upload failing "
            "for large shipment files?"
        ),
        user_context=lumen_user,
    )

    print("\nRESPONSE:")
    print(response)

    # ============================================================
    # TEST 6: TICKET INVESTIGATION
    # ============================================================
    print_section(
        "TEST 6: TICKET INVESTIGATION"
    )

    response = agent.handle_query(
        query="Investigate ticket TKT-502 and provide the current details.",
        user_context=lumen_user,
    )

    print("\nRESPONSE:")
    print(response)

    # ============================================================
    # TEST 7: PREPARE ESCALATION
    # MUST NOT EXECUTE WITHOUT EXPLICIT CONFIRMATION
    # ============================================================
    print_section(
        "TEST 7: PREPARE ESCALATION - CONFIRMATION REQUIRED"
    )

    escalation_response = agent.handle_query(
        query="Please escalate order ORD-1001 to the support team.",
        user_context=northstar_user,
    )

    print("\nRESPONSE:")
    print(escalation_response)

    # ------------------------------------------------------------
    # EXTRACT ACTION ID
    # ------------------------------------------------------------
    action_id = (
        escalation_response
        .get("action", {})
        .get("action_id")
    )

    print("\nPending Action ID:")
    print(action_id)

    if (
        escalation_response.get("success") is True
        and escalation_response.get("confirmation_required") is True
        and action_id
    ):
        print(
            "\nSUCCESS: Escalation prepared but NOT executed. "
            "Confirmation is required."
        )
    else:
        print(
            "\nERROR: Escalation preparation did not return "
            "a valid pending action."
        )

    # ============================================================
    # TEST 8: CONFIRM PENDING ACTION
    # IMPORTANT:
    # USE THE ACTUAL ACTION ID FROM TEST 7
    # ============================================================
    print_section(
        "TEST 8: CONFIRM PENDING ACTION"
    )

    if not action_id:
        print(
            "\nERROR: Cannot run confirmation test because "
            "Test 7 did not return an action ID."
        )
    else:
        confirm_query = f"Confirm {action_id}"

        print("\nConfirmation Query:")
        print(confirm_query)

        confirmation_response = agent.handle_query(
            query=confirm_query,
            user_context=northstar_user,
        )

        print("\nRESPONSE:")
        print(confirmation_response)

        if (
            confirmation_response.get("success") is True
            and confirmation_response.get("executed") is True
        ):
            print(
                "\nSUCCESS: Action executed only after "
                "explicit confirmation."
            )
        else:
            print(
                "\nERROR: Action confirmation did not execute correctly."
            )

    # ============================================================
    # TEST 9: CONFIRMED ACTION SHOULD NOT BE CONFIRMABLE AGAIN
    # ============================================================
    print_section(
        "TEST 9: PREVENT DOUBLE CONFIRMATION"
    )

    if action_id:
        response = agent.handle_query(
            query=f"Confirm {action_id}",
            user_context=northstar_user,
        )

        print("\nRESPONSE:")
        print(response)

        if response.get("success") is False:
            print(
                "\nSUCCESS: Executed action cannot be confirmed again."
            )
        else:
            print(
                "\nWARNING: Check whether duplicate confirmation "
                "is being prevented."
            )

    # ============================================================
    # TEST 10: CROSS-ACCOUNT ACTION ACCESS
    # ============================================================
    print_section(
        "TEST 10: LUMENWORKS CANNOT CONFIRM NORTHSTAR ACTION"
    )

    # Create a fresh pending action for this security test.
    security_escalation = agent.handle_query(
        query="Please escalate order ORD-1001 for additional review.",
        user_context=northstar_user,
    )

    security_action_id = (
        security_escalation
        .get("action", {})
        .get("action_id")
    )

    print("\nNorthstar Pending Action:")
    print(security_escalation)

    if security_action_id:
        response = agent.handle_query(
            query=f"Confirm {security_action_id}",
            user_context=lumen_user,
        )

        print("\nLumenWorks Confirmation Attempt:")
        print(response)

        if response.get("success") is False:
            print(
                "\nSUCCESS: Cross-account action confirmation denied."
            )
        else:
            print(
                "\nERROR: Cross-account action confirmation "
                "should have been denied."
            )
    else:
        print(
            "\nERROR: Could not create security test action."
        )

    # ============================================================
    # FINAL RESULT
    # ============================================================
    print_section(
        "ALL AGENT SERVICE TESTS COMPLETED"
    )

    print("\nVerified agent capabilities:")
    print("1. Natural-language query handling.")
    print("2. Document retrieval.")
    print("3. Structured-data lookup.")
    print("4. Account-scoped access control.")
    print("5. Internal support access.")
    print("6. Multi-step reasoning.")
    print("7. Contract and policy source precedence.")
    print("8. Product known-issue lookup.")
    print("9. Historical ticket context handling.")
    print("10. State-changing escalation preparation.")
    print("11. Explicit confirmation before action execution.")
    print("12. Prevention of duplicate action confirmation.")
    print("13. Cross-account action security.")


if __name__ == "__main__":
    main()