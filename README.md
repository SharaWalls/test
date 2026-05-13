# Data Engineering Exercise

## Overview

You are working with data from a fictional **Home Energy Management System (HEMS)** used by households with combinations of:
- grid connection
- rooftop solar
- home batteries
- EV chargers

The platform exposes API extracts containing:
- household metadata
- registered devices
- interval telemetry readings

This repository already includes a small local pipeline. It runs, reads the raw files, and writes an interval-level output. However, it has a number of intentional shortcomings.

You should expect to spend approximately **60-90 minutes** on this task.

## Task

Starting from the existing code in this repository, update the pipeline so that it is more useful for analytics.

The current starter implementation is intentionally incomplete and makes some simplistic assumptions. Your task is to improve it.

Please make the pipeline:
1. runnable locally
2. able to produce a cleaned interval-level curated dataset
3. able to produce a household daily summary dataset
4. reasonable in how it handles obvious data quality issues

You may use any tools you like. **PySpark is welcome, but not required.**

## What The Starter Already Does

The starter code currently:
- reads the raw files from `data/raw/`
- joins telemetry to device and household metadata
- writes a basic interval-level output to `output/`

It also has some intentional limitations. For example, it does not fully handle:
- mixed units such as `Wh` and `kWh`
- duplicate or corrected telemetry
- unknown or inactive devices
- local-date logic for New Zealand reporting
- tests beyond a very small starter set

## Requested Changes

Please update the code so that:
1. telemetry values are standardised in a sensible way
2. duplicate and corrected readings are handled reasonably
3. telemetry for unknown or inactive devices is handled appropriately
4. the curated outputs support household-level daily analysis
5. local date logic is appropriate for households in New Zealand
6. the transformation logic has at least a small amount of automated test coverage

You do not need to produce a perfect production system. We are more interested in your judgement, tradeoffs, and ability to work with an existing codebase.

## Expected Outputs

Please produce at least:
1. an cleaned interval-level curated dataset
2. a household daily summary dataset

Write outputs to the `output/` directory.

You may choose the exact schema, but it should support analysis of:
- household consumption
- solar generation
- battery usage
- grid import/export

## Raw Data

The supplied raw files are:
- `data/raw/households.csv`
- `data/raw/devices.json`
- `data/raw/telemetry.jsonl`

The telemetry file is JSON Lines formatted, with one JSON object per line.

## Assumptions

Assume households are in New Zealand and document any timezone assumptions you make.

The supplied data contains some intentional imperfections. Handle them in a reasonable way and document your assumptions.

## Deliverables

Please:
1. use this repository as your starting point
2. complete your solution within it
3. commit your work to your own **GitHub repository**
4. share the repository link with us

## README Requirements

Please include a short README covering:
- your approach and design decisions
- assumptions you made
- any known limitations
- what you would improve next if given more time
- how you would implement or run this in **Azure Databricks**

## Running Locally

Create and activate a virtual environment, then install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the pipeline:

```bash
./run.sh
```

The default runner calls:

```bash
python3 -m src.pipeline
```

Run the tests:

```bash
pytest -q
```

## Notes

We will use your submission as the basis for a follow-up discussion. Topics may include:
- why you changed the code the way you did
- how you would scale it
- how you would handle incremental processing
- how you would handle monitoring and alerting
- how you would handle late-arriving or corrected telemetry in production

## Repository Structure

```text
data-engineering-exercise/
├── README.md
├── data/
│   └── raw/
│       ├── households.csv
│       ├── devices.json
│       ├── telemetry.jsonl
├── src/
│   ├── __init__.py
│   ├── pipeline.py
│   ├── file_io.py
│   ├── transforms.py
│   └── constants.py
├── output/
├── tests/
├── requirements.txt
├── run.sh
└── .gitignore
```
