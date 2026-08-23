import pandas as pd

from backend.config import EXCEL_FILE


class SnapshotService:
    """
    Reads the official dataset reference time from the README sheet.

    All time-based calculations must use this timestamp instead of
    the machine's current time.
    """

    def __init__(self):
        self.snapshot_time = None
        self.currency = None

    def load_metadata(self):

        dataframe = pd.read_excel(
            EXCEL_FILE,
            sheet_name="README",
        )

        # The README contains:
        # Column 1 -> metadata key
        # Column 2 -> metadata value
        key_column = dataframe.columns[0]
        value_column = dataframe.columns[1]

        metadata = {}

        for _, row in dataframe.iterrows():

            key = str(row[key_column]).strip().lower()
            value = row[value_column]

            metadata[key] = value

        if "dataset snapshot" not in metadata:
            raise ValueError(
                "Dataset snapshot not found in README sheet."
            )

        raw_snapshot = str(
            metadata["dataset snapshot"]
        ).strip()

        # Example:
        # 2026-08-16 11:00 Asia/Kolkata
        parts = raw_snapshot.rsplit(
            " ",
            1,
        )

        if len(parts) != 2:
            raise ValueError(
                f"Invalid dataset snapshot format: "
                f"{raw_snapshot}"
            )

        datetime_text = parts[0]
        timezone_name = parts[1]

        # Parse only:
        # 2026-08-16 11:00
        snapshot = pd.to_datetime(
            datetime_text
        )

        # Add timezone:
        # Asia/Kolkata
        self.snapshot_time = snapshot.tz_localize(
            timezone_name
        )

        self.currency = str(
            metadata.get(
                "currency",
                "INR",
            )
        ).strip()

        return self.snapshot_time

    def get_snapshot_time(self):

        if self.snapshot_time is None:
            self.load_metadata()

        return self.snapshot_time

    def get_currency(self):

        if self.currency is None:
            self.load_metadata()

        return self.currency


snapshot_service = SnapshotService()


def get_snapshot_time():
    return snapshot_service.get_snapshot_time()


def get_currency():
    return snapshot_service.get_currency()