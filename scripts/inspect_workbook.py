import pandas as pd

from backend.config import EXCEL_FILE


def main():

    if not EXCEL_FILE.exists():

        print(
            f"ERROR: Workbook not found:\n{EXCEL_FILE}"
        )

        return

    excel = pd.ExcelFile(EXCEL_FILE)

    print("\n" + "=" * 70)
    print("PARCELPILOT WORKBOOK INSPECTION")
    print("=" * 70)

    print("\nSheets:")

    for sheet_name in excel.sheet_names:
        print(f" - {sheet_name}")

    for sheet_name in excel.sheet_names:

        dataframe = pd.read_excel(
            EXCEL_FILE,
            sheet_name=sheet_name,
        )

        print("\n" + "-" * 70)
        print(f"SHEET: {sheet_name}")
        print("-" * 70)

        print(
            f"\nRows: {len(dataframe)}"
        )

        print(
            f"Columns:\n{list(dataframe.columns)}"
        )

        print("\nFirst 5 rows:")

        print(
            dataframe.head().to_string()
        )


if __name__ == "__main__":
    main()