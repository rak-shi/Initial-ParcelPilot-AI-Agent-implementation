from backend.services.source_reliability import (
    get_source_metadata,
    is_authoritative,
    get_precedence_rank,
)


FILES = [
    "01_Support_Policy_v3_CURRENT.pdf",
    "02_Support_Policy_v2_DEPRECATED.pdf",
    "03_Cancellation_and_Service_Credit_SOP_v4.pdf",
    "04_Product_Operations_Guide_and_Known_Issues.pdf",
    "05_Northstar_Logistics_Enterprise_Agreement.pdf",
    "06_LumenWorks_Service_Agreement.pdf",
]


def main():

    print("\n" + "=" * 75)
    print("SOURCE RELIABILITY TEST")
    print("=" * 75)

    for filename in FILES:

        metadata = get_source_metadata(
            filename
        )

        print(f"\n{filename}")

        print(
            f"  Type: "
            f"{metadata['source_type']}"
        )

        print(
            f"  Status: "
            f"{metadata['status']}"
        )

        print(
            f"  Authority: "
            f"{get_precedence_rank(metadata)}"
        )

        print(
            f"  Authoritative: "
            f"{is_authoritative(metadata)}"
        )


if __name__ == "__main__":
    main()