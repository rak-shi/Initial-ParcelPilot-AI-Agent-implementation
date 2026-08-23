from backend.services.database_service import (
    DatabaseService,
)


def main():

    print("\nLoading ParcelPilot workbook...")

    database = DatabaseService()

    database.load_workbook()

    print(
        "\nSUCCESS: SQLite database created."
    )


if __name__ == "__main__":
    main()