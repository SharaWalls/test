"""Input/output helpers for the local starter pipeline."""

from pathlib import Path

import pandas as pd


def ensure_output_dir(path: Path) -> None:
    """Create the output directory if it does not already exist."""
    path.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> pd.DataFrame:
    """Read a CSV file into a DataFrame."""
    return pd.read_csv(path)


def read_json(path: Path) -> pd.DataFrame:
    """Read a JSON file into a DataFrame."""
    return pd.read_json(path)


def read_json_lines(path: Path) -> pd.DataFrame:
    """Read a JSON Lines file into a DataFrame."""
    return pd.read_json(path, lines=True)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    """Write a DataFrame to CSV."""
    df.to_csv(path, index=False)
