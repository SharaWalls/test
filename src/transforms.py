"""Transformation helpers for the starter pipeline.

The starter implementation is intentionally simple. It runs end to end but
leaves several quality issues unresolved so candidates can improve it.
"""

import pandas as pd
import pytz
from pathlib import Path


def save_rejected_records(df: pd.DataFrame, filename: str, reason: str):
    """Save rejected records to a separate file for audit trail"""
    if len(df) == 0:
        return
    
    rejected_dir = Path("output/rejected")
    rejected_dir.mkdir(parents=True, exist_ok=True)
    
    df_copy = df.copy()
    df_copy['rejected_reason'] = reason
    df_copy['rejected_at'] = pd.Timestamp.now().isoformat()
    
    output_path = rejected_dir / filename
    df_copy.to_csv(output_path, index=False)
    print(f"  Saved {len(df)} rejected records to {output_path}")


def standardize_telemetry_values(telemetry: pd.DataFrame) -> pd.DataFrame:
    """Add a value column for downstream use.
    
    IMPROVED: Now properly normalizes mixed units such as Wh and kWh.
    Also saves records with unknown units to rejected folder.
    """

    df = telemetry.copy()
    unknown_unit_mask = pd.Series(False, index=df.index)
    
    # Convert Wh to kWh if needed
    def convert_value(row):
        if pd.isna(row.get('unit')):
            return row['value']
        
        unit = row['unit'].lower()
        if unit == 'wh':
            return row['value'] / 1000.0
        elif unit == 'kwh':
            return row['value']
        else:
            # Mark as unknown for rejection
            nonlocal unknown_unit_mask
            unknown_unit_mask.at[row.name] = True
            return row['value']
    
    df["value_kwh"] = df.apply(convert_value, axis=1)
    
    # Save unknown unit records to rejected folder
    if 'unit' in df.columns:
        wh_count = (df['unit'].str.lower() == 'wh').sum()
        if wh_count > 0:
            print(f"INFO: Converted {wh_count} records from Wh to kWh")
        unknown_mask = ~df['unit'].str.lower().isin(['wh', 'kwh'])
        unknown_mask = unknown_mask | unknown_unit_mask
        unknown_records = df[unknown_mask].copy()
        if len(unknown_records) > 0:
            print(f"WARNING: Found {len(unknown_records)} records with unknown unit, saving to rejected")
            save_rejected_records(unknown_records, 'unknown_unit.csv', 'unknown unit in telemetry')
            df = df[~unknown_mask].copy()
    
    return df


def choose_latest_readings(telemetry: pd.DataFrame) -> pd.DataFrame:
    """Keep one row per reading identifier.
    
    IMPROVED: Now keeps the latest corrected version instead of earliest.
    """

    df = telemetry.copy()
    df["ingested_at"] = pd.to_datetime(df["ingested_at"], utc=True)
    # Changed from keep="first" to keep="last" to keep latest version
    df = df.sort_values(["reading_id", "ingested_at"])
    
    # Find and save duplicates before dropping
    duplicates = df[df.duplicated(subset=["reading_id"], keep=False)]
    if len(duplicates) > 0:
        duplicate_count = len(duplicates) - len(duplicates.drop_duplicates(subset=["reading_id"]))
        if duplicate_count > 0:
            print(f"INFO: Found {duplicate_count} duplicate records, keeping latest version")
            # Save duplicates to rejected folder
            dup_records = duplicates[duplicates.duplicated(subset=["reading_id"], keep='last')]
            if len(dup_records) > 0:
                save_rejected_records(dup_records, 'duplicates.csv', 'duplicate reading_id')
    
    return df.drop_duplicates(subset=["reading_id"], keep="last")


def enrich_telemetry(
    telemetry: pd.DataFrame,
    devices: pd.DataFrame,
    households: pd.DataFrame,
) -> pd.DataFrame:
    """Join telemetry to device and household metadata.
    
    IMPROVED: Now filters out unknown and inactive devices.
    """

    # Ensure consistent types
    telemetry['device_id'] = telemetry['device_id'].astype(str)
    devices['device_id'] = devices['device_id'].astype(str)
    
    # Filter unknown devices before join
    known_ids = set(devices['device_id'])
    is_known = telemetry['device_id'].isin(known_ids)
    unknown_records = telemetry[~is_known].copy()
    
    if len(unknown_records) > 0:
        unknown_devices = unknown_records['device_id'].unique()
        print(f"WARNING: Found {len(unknown_records)} records from unknown devices: {list(unknown_devices)}")
        save_rejected_records(unknown_records, 'unknown_devices.csv', 'device_id not in devices.json')
        telemetry = telemetry[is_known].copy()
    
    # Filter inactive devices
    active_ids = set(devices[devices['status'] == 'active']['device_id'])
    is_active = telemetry['device_id'].isin(active_ids)
    inactive_records = telemetry[~is_active].copy()
    
    if len(inactive_records) > 0:
        inactive_by_device = inactive_records.groupby('device_id').size()
        print(f"WARNING: Found {len(inactive_records)} records from inactive devices:")
        for device_id, count in inactive_by_device.items():
            print(f"           - {device_id}: {count} records")
        save_rejected_records(inactive_records, 'inactive_devices.csv', 'device status is not active')
        telemetry = telemetry[is_active].copy()
    
    # Handle missing values before join
    missing_mask = telemetry['value'].isna()
    missing_records = telemetry[missing_mask].copy()
    
    if len(missing_records) > 0:
        print(f"WARNING: Found {len(missing_records)} records with missing values")
        save_rejected_records(missing_records, 'missing_values.csv', 'value column is null')
        telemetry['value'] = telemetry['value'].fillna(0.0)
        telemetry['value_kwh'] = telemetry['value_kwh'].fillna(0.0)
    
    # Perform joins
    enriched = telemetry.merge(
        devices,
        on=["device_id", "household_id"],
        how="left",
    )
    enriched = enriched.merge(households, on="household_id", how="left")
    
    return enriched


def add_reporting_columns(intervals: pd.DataFrame) -> pd.DataFrame:
    """Add timestamp and reporting columns.
    
    IMPROVED: Now converts to New Zealand local time instead of using UTC.
    """

    df = intervals.copy()
    df["interval_start_utc"] = pd.to_datetime(df["interval_start_utc"], utc=True)
    df["interval_end_utc"] = pd.to_datetime(df["interval_end_utc"], utc=True)
    
    # Convert to New Zealand timezone
    nz_tz = pytz.timezone('Pacific/Auckland')
    
    def to_nz_date(utc_time):
        nz_time = utc_time.tz_convert(nz_tz)
        return nz_time.date()
    
    df["report_date"] = df["interval_start_utc"].apply(to_nz_date)
    
    # Also add local_date column for daily aggregation
    df["local_date"] = df["report_date"]
    
    failed = df['report_date'].isna().sum()
    if failed == 0:
        print(f"INFO: Added NZ local date column (timezone: Pacific/Auckland)")
    
    return df


def build_interval_dataset(
    households: pd.DataFrame,
    devices: pd.DataFrame,
    telemetry: pd.DataFrame,
) -> pd.DataFrame:
    """Build the starter interval-level dataset.
    
    IMPROVED: Now handles data quality issues properly.
    """

    print("\n" + "="*50)
    print("STARTING DATA CLEANING PIPELINE")
    print("="*50)
    print(f"Input: {len(telemetry)} telemetry records")
    
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
    
    result = reported[columns].sort_values(["household_id", "interval_start_utc", "device_id"])
    
    print("="*50)
    print(f"Output: {len(result)} clean records")
    print(f"Rejected records saved to: output/rejected/")
    print("="*50 + "\n")
    
    return result


def create_daily_summary(interval_df: pd.DataFrame) -> pd.DataFrame:
    """Generate household daily summary dataset."""
    
    print("\n" + "="*50)
    print("CREATING DAILY SUMMARY")
    print("="*50)
    
    # Group by household and local date
    summary = interval_df.groupby(['household_id', 'report_date']).agg(
        total_consumption_kwh=('value_kwh', 'sum'),
        record_count=('reading_id', 'count'),
        unique_devices=('device_id', 'nunique')
    ).reset_index()
    
    # Rename report_date to local_date for clarity
    summary = summary.rename(columns={'report_date': 'local_date'})
    
    # Round total_consumption_kwh to 2 decimal places
    summary['total_consumption_kwh'] = summary['total_consumption_kwh'].round(2)
    
    print(f"Created {len(summary)} daily records for {summary['household_id'].nunique()} households")
    print(f"Date range: {summary['local_date'].min()} to {summary['local_date'].max()}")
    print("="*50 + "\n")
    
    return summary
