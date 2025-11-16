import json
from pathlib import Path
from MRTD import encode_mrz


DECODED_FILE = Path("records_decoded.json")
ENCODED_FILE = Path("records_encoded.json")


def to_encode_fields(record: dict) -> dict:
    """
    Map one decoded record (with line1/line2) into the fields expected by encode_mrz().
    """
    line1 = record["line1"]
    line2 = record["line2"]

    return {
        "document_type": "P",                        # passports
        "issuing_state": line1["issuing_country"],
        "surname": line1["last_name"],
        "given_names": line1["given_name"],
        "passport_number": line2["passport_number"],
        "nationality": line2["country_code"],
        # birth/expiration are already 'YYMMDD' (e.g. "591010"), encode_mrz() will accept them
        "birth_date": line2["birth_date"],
        "sex": line2["sex"],
        "expiry_date": line2["expiration_date"],
        "personal_number": line2.get("personal_number", ""),
    }


def main():
    # Load the whole decoded file once
    with DECODED_FILE.open("r", encoding="utf-8") as fin:
        data = json.load(fin)

    records = data["records_decoded"]

    # Write encoded MRZ lines as newline-delimited JSON
    with ENCODED_FILE.open("w", encoding="utf-8") as fout:
        for rec in records:
            fields = to_encode_fields(rec)
            line1, line2 = encode_mrz(fields)

            # Assignment wants both lines separated by ';' in one JSON value
            json.dump({"mrz": f"{line1};{line2}"}, fout)
            fout.write("\n")

    print(f"Wrote {len(records)} encoded records to {ENCODED_FILE}")


if __name__ == "__main__":
    main()