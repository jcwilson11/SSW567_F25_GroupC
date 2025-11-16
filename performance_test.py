

import csv
import json
import time
from pathlib import Path

from MRTD import encode_mrz, decode_mrz, validate_mrz
from create_encoded_file import to_encode_fields

DECODED_FILE = Path("records_decoded.json")
ENCODED_FILE = Path("records_encoded.json")
CSV_FILE = Path("mrtd_timing.csv")

K_VALUES = [100] + list(range(1000, 10001, 1000))


def time_encode(records, k: int, with_tests: bool) -> float:
    """Time encoding the first k decoded records."""
    start = time.perf_counter()

    for rec in records[:k]:
        fields = to_encode_fields(rec)
        line1, line2 = encode_mrz(fields)

        if with_tests:
            # Lightweight unit-test style checks
            assert len(line1) == 44
            assert len(line2) == 44

    return time.perf_counter() - start


def time_decode(mrz_pairs, k: int, with_tests: bool) -> float:
    """Time decoding the first k encoded MRZ pairs."""
    start = time.perf_counter()

    for mrz in mrz_pairs[:k]:
        line1, line2 = mrz.split(";")

        if with_tests:
            # Full validation: recompute check digits and assert they match
            result = validate_mrz(line1, line2)
            assert result["valid"]
        else:
            # Baseline: just decode
            decode_mrz(line1, line2)

    return time.perf_counter() - start


def main():
    # ---- Preload decoded records ----
    with DECODED_FILE.open("r", encoding="utf-8") as fin:
        decoded_data = json.load(fin)
    decoded_records = decoded_data["records_decoded"]

    # ---- Preload encoded MRZ pairs ----
    mrz_pairs = []
    with ENCODED_FILE.open("r", encoding="utf-8") as fin:
        for line in fin:
            if line.strip():
                obj = json.loads(line)
                mrz_pairs.append(obj["mrz"])

    # ---- Run timings and write CSV ----
    with CSV_FILE.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "n_input",
            "enc_with_tests_s",
            "enc_no_tests_s",
            "dec_with_tests_s",
            "dec_no_tests_s",
        ])

        for k in K_VALUES:
            print(f"Measuring k={k}...")

            enc_with_tests = time_encode(decoded_records, k, with_tests=True)
            enc_no_tests   = time_encode(decoded_records, k, with_tests=False)
            dec_with_tests = time_decode(mrz_pairs, k, with_tests=True)
            dec_no_tests   = time_decode(mrz_pairs, k, with_tests=False)

            writer.writerow([
                k,
                enc_with_tests,
                enc_no_tests,
                dec_with_tests,
                dec_no_tests,
            ])

    print(f"Timing results written to {CSV_FILE}")


if __name__ == "__main__":
    main()
