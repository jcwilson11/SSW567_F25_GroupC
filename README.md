# SSW567_F25_GroupC

Machine Readable Travel Document (MRTD) utilities with encode/decode/validate functions, unit tests, and performance measurements.

## What this project does

Core MRTD functionality:

- `scan_mrz()`: software stub for a hardware MRZ scanner (defined, not implemented).
- `decode_mrz(line1, line2)`: parse TD3 passport MRZ lines into fields and extract check digits.
- `encode_mrz(fields)`: build TD3 MRZ lines from fields and embed check digits.
- `validate_mrz(line1, line2)`: recompute and report any check digit mismatches.
- `fletcher4_check_digit(data)`: single-digit Fletcher-4 (mod 10) check digit used by the above.

Notes:

- Format assumed is **ICAO TD3**: 2 lines, 44 chars each.
- Database stub: `query_document_fields(document_id)` is defined but not implemented.

Part 3 (Performance Testing):

- Encodes a large set of decoded passport records (`records_decoded.json`) into MRZ format (`records_encoded.json`).
- Measures encode/decode execution time for varying input sizes (`n = 100, 1000, 2000, …, 10000`).
- Compares **with-tests** vs **without-tests** versions of encoding and decoding.
- Outputs timing results to `mrtd_timing.csv` and (optionally) an Excel workbook with a performance plot.

---

## Repository layout

```text
SSW567_F25_GroupC/
  MRTD.py                      # Core MRTD implementation (encode/decode/validate)
  MTTDtest.py                  # pytest-based unit tests (with mocks for scanner/DB)

  create_encoded_file.py       # Part 3: generate records_encoded.json from records_decoded.json
  performance_test.py          # Part 3: run encode/decode timing experiments and write mrtd_timing.csv

  records_decoded.json         # Input data: decoded passport records (provided/fictitious)
  records_encoded.json         # Generated MRZ records (created by create_encoded_file.py)
  mrtd_timing.csv              # Timing measurements (created by performance_test.py)
  mrtd_timing_with_chart.xlsx  # (Optional) Excel workbook with timing data + performance chart

  MRTD_Performance_Report.docx # (Optional) Part 3 write-up/report
  README.md                    # this file
```

## Prerequisites

- Windows PowerShell (v5+)
- Python 3.7+ (3.10+ recommended)
- pip available on PATH

## Setup (create a virtual environment)

Option A: Python venv

```shell
# From the repository root
python -m venv .env
. .\.env\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install pytest pytest-cov
```

Option B: Conda

```shell
conda create -n mrtd python=3.7.9 -y
conda activate mrtd
pip install pytest pytest-cov
```

## Running tests

You have a pytest file.

```shell
python -m pytest -q SSW567_F25_GroupC\MTTDtest.py
```

- Optional: coverage for MRTD.py via pytest

```shell
python -m pytest --maxfail=1 -q --cov=MRTD --cov-report=term-missing SSW567_F25_GroupC\MTTDtest.py
```

This prints a table showing any lines not covered.

## Running a quick manual check

`MRTD.py` includes a small `__main__` block that generates an MRZ, prints both lines, and validates them.

```shell
python SSW567_F25_GroupC\MRTD.py
```

Part 3: Performance Testing Workflow

This section describes how to reproduce the Part 3 performance measurements.

1. Ensure input data is present

The file records_decoded.json must exist in the repository root.
It contains a JSON object with a records_decoded array, where each element looks like:

```json{
  "line1": {
    "issuing_country": "CIV",
    "last_name": "LYNN",
    "given_name": "NEVEAH BRAM"
  },
  "line2": {
    "passport_number": "W620126G5",
    "country_code": "CIV",
    "birth_date": "591010",
    "sex": "F",
    "expiration_date": "970730",
    "personal_number": "AJ010215I"
  }
}
```

Each record is mapped to the field names expected by encode_mrz().

2.Generate encoded MRZ data

Run the script that uses encode_mrz() to build MRZ lines for all decoded records and write them to records_encoded.json:

### From the repository root

```shell
python create_encoded_file.py
```

This will:

Read all entries under records_decoded["records_decoded"]

Call encode_mrz() for each one

Write a newline-delimited JSON file records_encoded.json where each line contains:

{"mrz": "LINE1;LINE2"}

3.Run performance measurements

Now run the timing experiment script:

```shell
python performance_test.py
```

This will:

Load all decoded records (for encoding timings)

Load all encoded MRZ pairs (for decoding timings)

For each n ∈ {100, 1000, 2000, …, 10000}:

Measure time for encoding with per-record assertions (encode with tests)

Measure time for encoding without assertions (encode without tests)

Measure time for decoding with full validation + assertions (decode with tests)

Measure time for decoding without validation (decode without tests)

Write results to mrtd_timing.csv with columns:

n_input,enc_with_tests_s,enc_no_tests_s,dec_with_tests_s,dec_no_tests_s

4.Plotting the results (Excel / Sheets)

You can either:

Option A: Use the provided Excel file

If mrtd_timing_with_chart.xlsx is present:

Open it in Excel.

The Timing Data sheet contains the data from mrtd_timing.csv.

A line chart is already embedded, showing:

Encode with tests

Encode without tests

Decode with tests

Decode without tests
as functions of n_input.

You can copy-paste this chart directly into your report.

Option B: Create your own plot

Open Excel → File → Open → select mrtd_timing.csv
(or import into Google Sheets).

Select all columns (including headers).

Insert → Line chart (or Scatter with lines).

Use:

X-axis: n_input

Y-axis series: the four timing columns.

Add axis labels and a chart title, e.g.
“MRTD Encode/Decode Performance vs Number of Records”.

## About hardware and database stubs

- scan_mrz(): defined but raises NotImplementedError (no actual hardware integration). In tests, it is mocked.
- query_document_fields(): defined but raises NotImplementedError (no real DB). In tests, it is mocked.

See `MTTDtest.py` for examples using `monkeypatch` to mock these functions.

## Troubleshooting

- "ModuleNotFoundError: No module named 'pytest'": install with `python -m pip install pytest` (or use the setup steps above).
- If pytest coverage flags are unrecognized, install plugin: `python -m pip install pytest-cov`.
- If PowerShell blocks script activation, open a new PowerShell as Administrator and run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then re-run the venv activation command.

## Contributors

Group members: Bowen Jiang, Emmanuel Okoro, Joris Wilson
