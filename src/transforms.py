"""Transformation helpers for the starter pipeline.

The starter implementation is intentionally simple. It runs end to end but
leaves several quality issues unresolved so candidates can improve it.
"""

import pandas as pd


def standardize_telemetry_values(telemetry: pd.DataFrame) -> pd.DataFrame:
    """Add a value column for downstream use.

    This starter implementation is intentionally naive and does not properly
    normalize mixed units such as Wh and kWh.
    """

    df = telemetry.copy()
    df["value_kwh"] = df["value"]
    return df


def choose_latest_readings(telemetry: pd.DataFrame) -> pd.DataFrame:
    """Keep one row per reading identifier.

    This implementation is intentionally simplistic and keeps the earliest
    version of a reading rather than the latest corrected version.
    """

    df = telemetry.copy()
    df["ingested_at"] = pd.to_datetime(df["ingested_at"], utc=True)
    df = df.sort_values(["reading_id", "ingested_at"])
    return df.drop_duplicates(subset=["reading_id"], keep="first")


def enrich_telemetry(
    telemetry: pd.DataFrame,
    devices: pd.DataFrame,
    households: pd.DataFrame,
) -> pd.DataFrame:
    """Join telemetry to device and household metadata."""

    enriched = telemetry.merge(
        devices,
        on=["device_id", "household_id"],
        how="left",
    )
    enriched = enriched.merge(households, on="household_id", how="left")
    return enriched


def add_reporting_columns(intervals: pd.DataFrame) -> pd.DataFrame:
    """Add timestamp and reporting columns.

    The local date is intentionally derived from UTC rather than converting to
    New Zealand local time first.
    """

    df = intervals.copy()
    df["interval_start_utc"] = pd.to_datetime(df["interval_start_utc"], utc=True)
    df["interval_end_utc"] = pd.to_datetime(df["interval_end_utc"], utc=True)
    df["report_date"] = df["interval_start_utc"].dt.date
    return df


def build_interval_dataset(
    households: pd.DataFrame,
    devices: pd.DataFrame,
    telemetry: pd.DataFrame,
) -> pd.DataFrame:
    """Build the starter interval-level dataset."""

    latest = choose_latest_readings(telemetry)
    standardized = standardize_telemetry_values(latest)
    enriched = enrich_telemetry(standardized, devices, households)
    reported = add_reporting_columns(enriched)

    columns = [
        "reading_id",
        "household_id",
        "device_id",
        "device_type",
        "status",
        "metric",
        "value",
        "value_kwh",
        "unit",
        "interval_start_utc",
        "interval_end_utc",
        "report_date",
        "region",
        "has_solar",
        "has_battery",
        "has_ev_charger",
        "ingested_at",
    ]
    return reported[columns].sort_values(["household_id", "interval_start_utc", "device_id"])
