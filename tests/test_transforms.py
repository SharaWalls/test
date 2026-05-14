import pandas as pd

from src.transforms import add_reporting_columns
from src.transforms import choose_latest_readings
from src.transforms import enrich_telemetry
from src.transforms import standardize_telemetry_values
from src.transforms import create_daily_summary


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


def test_standardize_telemetry_values_converts_wh_to_kwh() -> None:
    """Test that Wh values are correctly converted to kWh."""
    telemetry = pd.DataFrame(
        [
            {
                "reading_id": "R1",
                "value": 1000.0,
                "unit": "Wh",
            },
            {
                "reading_id": "R2",
                "value": 2.5,
                "unit": "kWh",
            },
            {
                "reading_id": "R3",
                "value": 500.0,
                "unit": "wh",  # lowercase
            },
        ]
    )

    actual = standardize_telemetry_values(telemetry)

    assert "value_kwh" in actual.columns
    assert actual.loc[0, "value_kwh"] == 1.0  # 1000 Wh -> 1 kWh
    assert actual.loc[1, "value_kwh"] == 2.5  # already kWh
    assert actual.loc[2, "value_kwh"] == 0.5  # 500 Wh -> 0.5 kWh


def test_enrich_telemetry_adds_device_and_household_columns() -> None:
    telemetry = pd.DataFrame(
        [
            {
                "reading_id": "R1",
                "device_id": "DEV1",
                "household_id": "HH1",
                "value": 1.0,
                "value_kwh": 1.0,
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


# New test for create_daily_summary
def test_create_daily_summary_aggregates_correctly() -> None:
    """Test that daily summary correctly aggregates interval data by household and date."""
    
    # Create sample interval data
    interval_df = pd.DataFrame(
        [
            {
                "reading_id": "R1",
                "household_id": "HH1",
                "device_id": "DEV1",
                "value_kwh": 1.5,
                "report_date": pd.Timestamp("2026-02-01").date(),
                "interval_start_utc": "2026-02-01T00:00:00Z",
            },
            {
                "reading_id": "R2",
                "household_id": "HH1",
                "device_id": "DEV2",
                "value_kwh": 2.5,
                "report_date": pd.Timestamp("2026-02-01").date(),
                "interval_start_utc": "2026-02-01T01:00:00Z",
            },
            {
                "reading_id": "R3",
                "household_id": "HH1",
                "device_id": "DEV1",
                "value_kwh": 1.0,
                "report_date": pd.Timestamp("2026-02-02").date(),
                "interval_start_utc": "2026-02-02T00:00:00Z",
            },
            {
                "reading_id": "R4",
                "household_id": "HH2",
                "device_id": "DEV3",
                "value_kwh": 3.0,
                "report_date": pd.Timestamp("2026-02-01").date(),
                "interval_start_utc": "2026-02-01T00:00:00Z",
            },
        ]
    )
    
    actual = create_daily_summary(interval_df)
    
    # Should have 3 rows: HH1 on 2026-02-01, HH1 on 2026-02-02, HH2 on 2026-02-01
    assert len(actual) == 3
    
    # Check HH1 on 2026-02-01
    hh1_day1 = actual[(actual['household_id'] == 'HH1') & (actual['local_date'] == pd.Timestamp("2026-02-01").date())]
    assert len(hh1_day1) == 1
    assert hh1_day1.iloc[0]['total_consumption_kwh'] == 4.0  # 1.5 + 2.5
    assert hh1_day1.iloc[0]['record_count'] == 2
    assert hh1_day1.iloc[0]['unique_devices'] == 2
    
    # Check HH1 on 2026-02-02
    hh1_day2 = actual[(actual['household_id'] == 'HH1') & (actual['local_date'] == pd.Timestamp("2026-02-02").date())]
    assert len(hh1_day2) == 1
    assert hh1_day2.iloc[0]['total_consumption_kwh'] == 1.0
    assert hh1_day2.iloc[0]['record_count'] == 1
    assert hh1_day2.iloc[0]['unique_devices'] == 1
    
    # Check HH2 on 2026-02-01
    hh2_day1 = actual[(actual['household_id'] == 'HH2') & (actual['local_date'] == pd.Timestamp("2026-02-01").date())]
    assert len(hh2_day1) == 1
    assert hh2_day1.iloc[0]['total_consumption_kwh'] == 3.0
    assert hh2_day1.iloc[0]['record_count'] == 1
    assert hh2_day1.iloc[0]['unique_devices'] == 1


def test_create_daily_summary_handles_empty_dataframe() -> None:
    """Test that create_daily_summary handles empty input gracefully."""
    
    empty_df = pd.DataFrame(columns=['household_id', 'report_date', 'value_kwh', 'reading_id', 'device_id'])
    
    actual = create_daily_summary(empty_df)
    
    # Should return empty dataframe with expected columns
    assert len(actual) == 0
    assert 'household_id' in actual.columns
    assert 'local_date' in actual.columns
    assert 'total_consumption_kwh' in actual.columns
    assert 'record_count' in actual.columns
    assert 'unique_devices' in actual.columns
