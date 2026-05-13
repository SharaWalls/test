import pandas as pd

from src.transforms import add_reporting_columns
from src.transforms import choose_latest_readings
from src.transforms import enrich_telemetry


def test_choose_latest_readings_keeps_one_row_per_reading_id() -> None:
    telemetry = pd.DataFrame(
        [
            {
                "reading_id": "R1",
                "ingested_at": "2026-02-01T00:35:00Z",
                "value": 1.0,
            },
            {
                "reading_id": "R1",
                "ingested_at": "2026-02-01T00:36:00Z",
                "value": 1.1,
            },
            {
                "reading_id": "R2",
                "ingested_at": "2026-02-01T00:35:00Z",
                "value": 2.0,
            },
        ]
    )

    actual = choose_latest_readings(telemetry)

    assert len(actual) == 2
    assert set(actual["reading_id"]) == {"R1", "R2"}


def test_enrich_telemetry_adds_device_and_household_columns() -> None:
    telemetry = pd.DataFrame(
        [
            {
                "reading_id": "R1",
                "device_id": "DEV1",
                "household_id": "HH1",
            }
        ]
    )
    devices = pd.DataFrame(
        [
            {
                "device_id": "DEV1",
                "household_id": "HH1",
                "device_type": "grid_meter",
                "status": "active",
            }
        ]
    )
    households = pd.DataFrame(
        [
            {
                "household_id": "HH1",
                "region": "Wellington",
            }
        ]
    )

    actual = enrich_telemetry(telemetry, devices, households)

    assert actual.loc[0, "device_type"] == "grid_meter"
    assert actual.loc[0, "region"] == "Wellington"


def test_add_reporting_columns_adds_report_date() -> None:
    intervals = pd.DataFrame(
        [
            {
                "interval_start_utc": "2026-02-01T23:30:00Z",
                "interval_end_utc": "2026-02-02T00:00:00Z",
            }
        ]
    )

    actual = add_reporting_columns(intervals)

    assert "report_date" in actual.columns
