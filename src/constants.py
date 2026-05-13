"""Project constants and shared configuration values."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "output"

HOUSEHOLDS_PATH = RAW_DIR / "households.csv"
DEVICES_PATH = RAW_DIR / "devices.json"
TELEMETRY_PATH = RAW_DIR / "telemetry.jsonl"

NZ_TIMEZONE = "Pacific/Auckland"
