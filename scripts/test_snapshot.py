from backend.services.snapshot_service import (
    get_snapshot_time,
    get_currency,
)


def main():

    snapshot_time = get_snapshot_time()
    currency = get_currency()

    print("\n" + "=" * 60)
    print("PARCELPILOT DATASET METADATA")
    print("=" * 60)

    print(f"Snapshot Time: {snapshot_time}")
    print(f"Currency: {currency}")


if __name__ == "__main__":
    main()