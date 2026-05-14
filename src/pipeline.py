"""Pipeline entry point for the starter implementation."""

from src.constants import DEVICES_PATH
from src.constants import HOUSEHOLDS_PATH
from src.constants import OUTPUT_DIR
from src.constants import TELEMETRY_PATH
from src.file_io import ensure_output_dir
from src.file_io import read_csv
from src.file_io import read_json
from src.file_io import read_json_lines
from src.file_io import write_csv
from src.transforms import build_interval_dataset, create_daily_summary  


def run_pipeline() -> None:
    """Run the starter local pipeline."""

    ensure_output_dir(OUTPUT_DIR)

    households = read_csv(HOUSEHOLDS_PATH)
    devices = read_json(DEVICES_PATH)
    telemetry = read_json_lines(TELEMETRY_PATH)

  
    interval_dataset = build_interval_dataset(
        households=households,
        devices=devices,
        telemetry=telemetry,
    )
    

    write_csv(interval_dataset, OUTPUT_DIR / "interval_cleaned.csv") 


    daily_summary = create_daily_summary(interval_dataset)
    

    write_csv(daily_summary, OUTPUT_DIR / "daily_summary.csv")

    print(f"    -ipeline completed!")
    print(f"   - Interval data: {OUTPUT_DIR / 'interval_cleaned.csv'}")
    print(f"   - Daily summary: {OUTPUT_DIR / 'daily_summary.csv'}")
    print(f"   - Rejected records: {OUTPUT_DIR / 'rejected/'}")


if __name__ == "__main__":
    run_pipeline()
