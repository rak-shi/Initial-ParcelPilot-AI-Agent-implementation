from backend.services.document_service import DocumentService
from backend.services.auth_service import get_user_context


def print_results(title, results):

    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    if not results:
        print("No results found.")
        return

    for index, result in enumerate(results, start=1):

        metadata = result["metadata"]

        print(f"\nRESULT {index}")

        print(f"Source: {metadata.get('filename')}")
        print(f"Page: {metadata.get('page_number')}")
        print(f"Authority: {metadata.get('authority')}")
        print(f"Scope: {metadata.get('scope')}")
        print(
            f"Account ID: "
            f"{metadata.get('account_id') or 'GLOBAL'}"
        )
        print(
            f"Similarity: "
            f"{result.get('similarity', 0):.4f}"
        )

        print("\nContent:")
        print(result["content"][:700])

        print("\n" + "-" * 80)


def main():

    service = DocumentService()

    # ==========================================
    # TEST 1: NORTHSTAR CUSTOMER
    # ==========================================

    northstar_user = get_user_context(
        "northstar_customer"
    )

    results = service.search(
        query=(
            "Can I cancel a shipment without "
            "paying a cancellation fee?"
        ),
        user_context=northstar_user,
        account_id="ACCT-001",
    )

    print_results(
        "TEST 1: NORTHSTAR CUSTOMER",
        results,
    )

    # ==========================================
    # TEST 2: LUMENWORKS CUSTOMER
    # ==========================================

    lumen_user = get_user_context(
        "lumen_customer"
    )

    results = service.search(
        query=(
            "What are the cancellation and "
            "service credit terms?"
        ),
        user_context=lumen_user,
        account_id="ACCT-002",
    )

    print_results(
        "TEST 2: LUMENWORKS CUSTOMER",
        results,
    )

    # ==========================================
    # TEST 3: SECURITY TEST
    # Northstar must NOT see LumenWorks agreement
    # ==========================================

    results = service.search(
        query=(
            "LumenWorks agreement "
            "service credit terms"
        ),
        user_context=northstar_user,
    )

    print_results(
        "TEST 3: SECURITY - NORTHSTAR "
        "SEARCHING FOR LUMENWORKS",
        results,
    )

    # ==========================================
    # TEST 4: INTERNAL SUPPORT
    # ==========================================

    support_user = get_user_context(
        "support_agent"
    )

    results = service.search(
        query=(
            "LumenWorks agreement "
            "service credit terms"
        ),
        user_context=support_user,
        account_id="ACCT-002",
    )

    print_results(
        "TEST 4: INTERNAL SUPPORT",
        results,
    )


if __name__ == "__main__":
    main()