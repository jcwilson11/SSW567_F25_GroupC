# SSW567_F25_GroupC

Machine Readable Travel Document (MRTD) utilities with encode/decode/validate functions and tests.

## What this project does

- scan_mrz(): software stub for a hardware MRZ scanner (defined, not implemented)
- decode_mrz(line1, line2): parse TD3 passport MRZ lines into fields and extract check digits
- encode_mrz(fields): build TD3 MRZ lines from fields and embed check digits
- validate_mrz(line1, line2): recompute and report any check digit mismatches
- fletcher4_check_digit(data): single-digit Fletcher-4 (mod 10) check digit used by the above

Notes:

- Format assumed is ICAO TD3: 2 lines, 44 chars each.
- Database stub: query_document_fields(document_id) is defined but not implemented.


## Repository layout

```text
SSW567_F25_GroupC/
  MRTD.py           # Implementation
  MTTDtest.py       # pytest-based tests (with mocks for scanner/DB)
  README.md         # this file
```

## Prerequisites

- Windows PowerShell (v5+)
- Python 3.7+ (3.10+ recommended)
- pip available on PATH

## Setup (create a virtual environment)

Option A: Python venv

```powershell
# From the repository root
python -m venv .env
. .\.env\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install pytest pytest-cov
```

Option B: Conda

```powershell
conda create -n mrtd python=3.10 -y
conda activate mrtd
pip install pytest pytest-cov
```

## Running tests

You have a pytest file.

```powershell
python -m pytest -q SSW567_F25_GroupC\MTTDtest.py
```

- Optional: coverage for MRTD.py via pytest

```powershell
python -m pytest --maxfail=1 -q --cov=MRTD --cov-report=term-missing SSW567_F25_GroupC\MTTDtest.py
```

This prints a table showing any lines not covered.

## Running a quick manual check

`MRTD.py` includes a small `__main__` block that generates an MRZ, prints both lines, and validates them.

```powershell
python SSW567_F25_GroupC\MRTD.py
```

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
