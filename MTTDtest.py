import pytest
import MRTD

from MRTD import (
    scan_mrz,
    query_document_fields,
    encode_mrz,
    decode_mrz,
    validate_mrz,
    fletcher4_check_digit,
)


# This test verifies that the scanner function is defined but not implemented,
# and that calling it without a hardware implementation raises NotImplementedError.
def test_scan_mrz_not_implemented_raises():
    with pytest.raises(NotImplementedError):
        scan_mrz()


# This test uses monkeypatch to mock the hardware scanner function, simulating
# the return of two MRZ lines. It ensures our test harness can work without hardware.
def test_scan_mrz_mocked_returns_lines(monkeypatch):
    sample_fields = {
        'document_type': 'P',
        'issuing_state': 'USA',
        'surname': 'DOE',
        'given_names': 'JANE MARIE',
        'passport_number': '123456789',
        'nationality': 'USA',
        'birth_date': '1990-07-05',
        'sex': 'F',
        'expiry_date': '2030-01-31',
        'personal_number': 'ABC123',
    }
    line1, line2 = encode_mrz(sample_fields)

    # Monkeypatch the scan function to return our generated lines
    monkeypatch.setattr('MRTD.scan_mrz', lambda: (line1, line2))

    # Call through the module so the monkeypatch applies
    l1, l2 = MRTD.scan_mrz()
    assert l1 == line1 and l2 == line2


# This test checks a full encode -> decode -> validate round-trip for correctness
# and ensures validate_mrz reports no mismatches for correct data.
def test_encode_decode_validate_round_trip():
    fields = {
        'document_type': 'P',
        'issuing_state': 'USA',
        'surname': 'DOE',
        'given_names': 'JANE MARIE',
        'passport_number': '123456789',
        'nationality': 'USA',
        'birth_date': '1990-07-05',
        'sex': 'F',
        'expiry_date': '2030-01-31',
        'personal_number': 'ABC123',
    }
    l1, l2 = encode_mrz(fields)
    parsed = decode_mrz(l1, l2)

    assert len(l1) == 44 and len(l2) == 44
    assert parsed['document_type'].startswith('P')
    assert parsed['issuing_state'][:3] == 'USA'
    assert parsed['passport_number'] == '123456789'
    assert parsed['nationality'] == 'USA'
    assert parsed['birth_date'] == '900705'  # YYMMDD from 1990-07-05
    assert parsed['sex'] == 'F'
    assert parsed['expiry_date'] == '300131'  # YYMMDD from 2030-01-31

    result = validate_mrz(l1, l2)
    assert result['valid'] is True
    assert result['mismatches'] == []


# This test ensures the name formatting rules (using '<' as separators) are
# handled during encoding and properly decoded back to spaces for readability.
def test_decode_parses_names():
    fields = {
        'document_type': 'P',
        'issuing_state': 'NLD',
        'surname': 'van der Waals',
        'given_names': 'Anna-Maria',
        'passport_number': 'X1234567',
        'nationality': 'NLD',
        'birth_date': '1985-12-24',
        'sex': 'F',
        'expiry_date': '2032-08-15',
        'personal_number': '',
    }
    l1, l2 = encode_mrz(fields)
    parsed = decode_mrz(l1, l2)

    assert 'VAN' in parsed['surname']
    assert 'ANNA' in parsed['given_names']


# This test corrupts the passport number check digit to confirm
# validate_mrz flags the correct field mismatch.
def test_validate_detects_passport_cd_mismatch():
    fields = {
        'document_type': 'P',
        'issuing_state': 'USA',
        'surname': 'DOE',
        'given_names': 'JOHN',
        'passport_number': '555555555',
        'nationality': 'USA',
        'birth_date': '1999-09-09',
        'sex': 'M',
        'expiry_date': '2031-09-09',
        'personal_number': '',
    }
    l1, l2 = encode_mrz(fields)
    # Change the passport number check digit at position 9
    bad_cd = '0' if l2[9] != '0' else '1'
    l2_bad = l2[:9] + bad_cd + l2[10:]

    result = validate_mrz(l1, l2_bad)
    assert result['valid'] is False
    assert 'passport_number check digit mismatch' in result['mismatches']


# This test corrupts the final composite check digit to confirm
# validate_mrz specifically detects composite mismatches.
def test_validate_detects_composite_cd_mismatch():
    fields = {
        'document_type': 'P',
        'issuing_state': 'USA',
        'surname': 'DOE',
        'given_names': 'ALAN',
        'passport_number': 'A1B2C3D4E',
        'nationality': 'USA',
        'birth_date': '1970-01-01',
        'sex': 'M',
        'expiry_date': '2030-01-01',
        'personal_number': 'XYZ',
    }
    l1, l2 = encode_mrz(fields)
    # Corrupt last character (composite check digit) at position 43
    bad_last = '9' if l2[43] != '9' else '0'
    l2_bad = l2[:43] + bad_last

    result = validate_mrz(l1, l2_bad)
    assert result['valid'] is False
    assert 'composite check digit mismatch' in result['mismatches']


# This test verifies that date inputs in 'YYYY-MM-DD' are converted to 'YYMMDD'
# in the MRZ, by checking parsed birth and expiry dates after decode.
def test_date_formats_are_converted():
    fields = {
        'document_type': 'P',
        'issuing_state': 'GBR',
        'surname': 'SMITH',
        'given_names': 'EMMA',
        'passport_number': '987654321',
        'nationality': 'GBR',
        'birth_date': '2001-02-03',
        'sex': 'F',
        'expiry_date': '2044-05-06',
        'personal_number': '',
    }
    l1, l2 = encode_mrz(fields)
    parsed = decode_mrz(l1, l2)

    assert parsed['birth_date'] == '010203'
    assert parsed['expiry_date'] == '440506'


# This test verifies that invalid/unknown sex values default to '<' in the MRZ
# and are decoded as such.
def test_sex_invalid_defaults():
    fields = {
        'document_type': 'P',
        'issuing_state': 'CAN',
        'surname': 'LEE',
        'given_names': 'TAYLOR',
        'passport_number': 'QWERTY123',
        'nationality': 'CAN',
        'birth_date': '1995-03-17',
        'sex': 'U',  # invalid -> should default to '<'
        'expiry_date': '2030-03-17',
        'personal_number': '',
    }
    l1, l2 = encode_mrz(fields)
    parsed = decode_mrz(l1, l2)

    assert parsed['sex'] == '<'


# This test checks the Fletcher-4 check digit implementation on a known string
# by re-computing the expected value manually and comparing.
# String: 'ABC123<' should yield check digit '1' with our mod-10 Fletcher variant.
def test_fletcher4_check_digit_known_value():
    assert fletcher4_check_digit('ABC123<') == '1'


# This test demonstrates mocking a database access function to get document fields.
# We monkeypatch query_document_fields to return a fake record and then encode and validate.
@pytest.mark.usefixtures("monkeypatch")
def test_query_document_fields_mock_encode_validate(monkeypatch):
    def fake_query(doc_id: str):
        return {
            'document_type': 'P',
            'issuing_state': 'USA',
            'surname': 'DOE',
            'given_names': 'JANE',
            'passport_number': 'ZZZ999888',
            'nationality': 'USA',
            'birth_date': '1992-11-30',
            'sex': 'F',
            'expiry_date': '2032-11-30',
            'personal_number': 'PN12345',
        }

    # Monkeypatch the DB function in the MRTD module
    monkeypatch.setattr('MRTD.query_document_fields', fake_query)

    # Call through the module so the monkeypatch applies
    fields = MRTD.query_document_fields('DOC-12345')
    l1, l2 = encode_mrz(fields)
    result = validate_mrz(l1, l2)

    assert len(l1) == 44 and len(l2) == 44
    assert result['valid'] is True
    assert result['mismatches'] == []


# ---------------------------------------------------------------------------
# Additional tests using nationality/issuing codes from ISO/ICAO Doc 9303 lists
# (British categories, Germany, Kosovo, EU). Some are 3-letter (e.g., GBD, RKS,
# EUE) and some are 1-2 letter (e.g., D, DE, EU). Our encoder pads 1-2 letter
# codes with '<' to fit 3 characters, which is what the MRZ requires.
# ---------------------------------------------------------------------------

# This test verifies that 3-letter special codes round-trip exactly for both
# nationality and issuing_state.
@pytest.mark.parametrize("code", [
    "GBD",  # British Overseas Territories Citizen
    "GBN",  # British National (Overseas)
    "GBO",  # British Overseas Citizen
    "GBS",  # British Subject
    "GBP",  # British Protected Person
    "RKS",  # Kosovo (3-letter)
    "EUE",  # European Union (3-letter reserved)
])
def test_three_letter_special_codes_round_trip(code):
    fields = {
        'document_type': 'P',
        'issuing_state': code,
        'surname': 'TESTER',
        'given_names': 'ALPHA',
        'passport_number': 'A1B2C3D4E',
        'nationality': code,
        'birth_date': '1991-01-02',
        'sex': 'M',
        'expiry_date': '2031-01-02',
        'personal_number': '',
    }
    l1, l2 = encode_mrz(fields)
    parsed = decode_mrz(l1, l2)
    # Expect exact 3-letter codes preserved
    assert parsed['issuing_state'] == code
    assert parsed['nationality'] == code
    # And overall MRZ validates
    assert validate_mrz(l1, l2)['valid'] is True


# This test verifies that 1-2 letter codes are padded with '<' to 3 characters
# when encoded in MRZ, for both nationality and issuing_state.
@pytest.mark.parametrize("short_code,expected", [
    ("D",  "D<<"),  # Germany (1-letter per table), becomes D<< in MRZ
    ("DE", "DE<"),  # Germany (2-letter), becomes DE< in MRZ
    ("EU", "EU<"),  # European Union (2-letter), becomes EU< in MRZ
    ("KS", "KS<"),  # Kosovo (2-letter), becomes KS< in MRZ
])
def test_short_codes_are_padded(short_code, expected):
    fields = {
        'document_type': 'P',
        'issuing_state': short_code,
        'surname': 'SIGMA',
        'given_names': 'BETA',
        'passport_number': 'Z9Y8X7W6V',
        'nationality': short_code,
        'birth_date': '1980-06-15',
        'sex': 'F',
        'expiry_date': '2030-06-15',
        'personal_number': '',
    }
    l1, l2 = encode_mrz(fields)
    parsed = decode_mrz(l1, l2)
    # Expect padding with '<' to length 3
    assert parsed['issuing_state'] == expected
    assert parsed['nationality'] == expected
    # Still should validate under Fletcher-4 checks
    assert validate_mrz(l1, l2)['valid'] is True

# Additioanl Mutant-killing testing: current rate is 52% killed
# ------------------------------
# Independent checksum oracle
# ------------------------------
def _mrz_val(ch: str) -> int:
    c = (ch or "<").upper()
    if "0" <= c <= "9":
        return ord(c) - ord("0")
    if "A" <= c <= "Z":
        return 10 + ord(c) - ord("A")
    if c == "<":
        return 0
    return 0

def fletcher4_ref(data: str) -> str:
    s1 = 0
    s2 = 0
    for ch in data:
        v = _mrz_val(ch)
        s1 = (s1 + v) % 10
        s2 = (s2 + s1) % 10
    return str((s1 + s2) % 10)

@pytest.mark.parametrize("payload", [
    "",                 # all filler
    "<",                # single filler
    "A",                # single letter
    "0",                # single digit
    "ABC123<",          # mixed
    "ZZZZZZZZZ",        # worst-case high letters
    "9Z<5A0<<<<<123",   # varied
    "<"*20,             # long filler
])
def test_fletcher4_matches_reference(payload):
    assert fletcher4_check_digit(payload) == fletcher4_ref(payload)

# ------------------------------
# Helpers
# ------------------------------
BASE_FIELDS = {
    "document_type": "P",
    "issuing_state": "USA",
    "surname": "DOE",
    "given_names": "JANE MARIE",
    "passport_number": "123456789",
    "nationality": "USA",
    "birth_date": "1990-07-05",
    "sex": "F",
    "expiry_date": "2030-01-31",
    "personal_number": "ABC123",
}

def flip_digit_char(ch: str) -> str:
    # simple deterministic flip to ensure a single-char tamper
    if ch.isdigit():
        return "0" if ch != "0" else "1"
    if ch == "<":
        return "A"
    # letter
    return "Z" if ch != "Z" else "A"

# ------------------------------
# Single-field tamper tests
# ------------------------------
def test_tamper_passport_number_cd_triggers_mismatch():
    l1, l2 = encode_mrz(BASE_FIELDS)
    # flip the passport-number CD at index 9
    l2_bad = l2[:9] + flip_digit_char(l2[9]) + l2[10:]
    out = validate_mrz(l1, l2_bad)
    assert out["valid"] is False
    assert "passport_number check digit mismatch" in out["mismatches"]

def test_tamper_birth_date_cd_triggers_mismatch():
    l1, l2 = encode_mrz(BASE_FIELDS)
    l2_bad = l2[:19] + flip_digit_char(l2[19]) + l2[20:]
    out = validate_mrz(l1, l2_bad)
    assert out["valid"] is False
    assert "birth_date check digit mismatch" in out["mismatches"]

def test_tamper_expiry_date_cd_triggers_mismatch():
    l1, l2 = encode_mrz(BASE_FIELDS)
    l2_bad = l2[:27] + flip_digit_char(l2[27]) + l2[28:]
    out = validate_mrz(l1, l2_bad)
    assert out["valid"] is False
    assert "expiry_date check digit mismatch" in out["mismatches"]

def test_tamper_personal_number_cd_triggers_mismatch():
    l1, l2 = encode_mrz(BASE_FIELDS)
    l2_bad = l2[:42] + flip_digit_char(l2[42]) + l2[43:]
    out = validate_mrz(l1, l2_bad)
    assert out["valid"] is False
    assert "personal_number check digit mismatch" in out["mismatches"]

def test_tamper_composite_cd_triggers_mismatch():
    l1, l2 = encode_mrz(BASE_FIELDS)
    l2_bad = l2[:43] + flip_digit_char(l2[43])
    out = validate_mrz(l1, l2_bad)
    assert out["valid"] is False
    assert "composite check digit mismatch" in out["mismatches"]




# ------------------------------
# Structural / positioning checks
# ------------------------------
def test_line2_field_positions_and_lengths_are_stable():
    l1, l2 = encode_mrz(BASE_FIELDS)
    assert len(l1) == 44 and len(l2) == 44

    # Slices per TD3 layout implemented in MRTD.decode_mrz
    parsed = decode_mrz(l1, l2)
    # confirm slices align with encode inputs after canonicalization
    assert parsed["passport_number"] == "123456789"
    assert parsed["nationality"] == "USA"
    assert parsed["birth_date"] == "900705"
    assert parsed["sex"] == "F"
    assert parsed["expiry_date"] == "300131"
    assert len(parsed["personal_number"]) == 14  # padded to 14 with '<'
    # check that any leftover is padding
    trailing = l2[44:]  # should be empty
    assert trailing == ""

def test_name_sanitization_and_padding_boundaries():
    fields = dict(BASE_FIELDS)
    fields["surname"] = "van der Wååls!?"
    fields["given_names"] = "Anna-María  O'Neil  Jr."
    # also push boundary: very long names should truncate to fit 39 chars in line1 name field
    fields["given_names"] += " " + ("X"*60)
    l1, _ = encode_mrz(fields)
    # line1: 2 + 3 + 39 = 44
    assert len(l1) == 44
    # decode back to human-readable (spaces for '<'), no punctuation outside A-Z0-9 survives
    parsed = decode_mrz(l1, "<<"*22)  # dummy line2, decode only line1 fields we care about
    assert "VAN" in parsed["surname"]  # diacritics stripped
    assert "ONEIL" in parsed["given_names"]  # apostrophe removed
    # There must be a '<<' between surname and given names per encoder
    assert "  " not in l1[5:44]  # no double-spaces; separators are '<'

# ------------------------------
# Date format/validation edges
# ------------------------------



def test_date_accepts_yymmdd_passthrough_and_yyyy_mm_dd():
    f = dict(BASE_FIELDS)
    f["birth_date"] = "900705"   # passthrough
    f["expiry_date"] = "2030/01/31"
    l1, l2 = encode_mrz(f)
    p = decode_mrz(l1, l2)
    assert p["birth_date"] == "900705"
    assert p["expiry_date"] == "300131"

# ------------------------------
# Sex normalization (ROR/LCR)
# ------------------------------
@pytest.mark.parametrize("inp,expected", [
    ("m", "M"), ("F", "F"), ("x", "X"), ("?", "<"), ("", "<")
])
def test_sex_normalization_and_default(inp, expected):
    f = dict(BASE_FIELDS)
    f["sex"] = inp
    l1, l2 = encode_mrz(f)
    p = decode_mrz(l1, l2)
    assert p["sex"] == expected

# ------------------------------
# Padding/truncation for codes and numbers
# ------------------------------
@pytest.mark.parametrize("code,expected", [
    ("D", "D<<"),
    ("DE", "DE<"),
    ("", "<<<"),
])
def test_issuing_and_nationality_padding(code, expected):
    f = dict(BASE_FIELDS)
    f["issuing_state"] = code
    f["nationality"] = code
    l1, l2 = encode_mrz(f)
    p = decode_mrz(l1, l2)
    assert p["issuing_state"] == expected
    assert p["nationality"] == expected

def test_passport_number_length_truncates_and_rechecks():
    f = dict(BASE_FIELDS)
    f["passport_number"] = "A123456789XYZ"  # >9, must truncate to 9
    l1, l2 = encode_mrz(f)
    p = decode_mrz(l1, l2)
    assert p["passport_number"] == "A12345678"  # first 9 after truncation
    # And the CD must match the truncated data
    assert fletcher4_check_digit(p["passport_number"]) == p["passport_number_cd"]
    assert validate_mrz(l1, l2)["valid"] is True

def test_personal_number_padding_and_cd_consistency():
    f = dict(BASE_FIELDS)
    f["personal_number"] = "X1"  # should pad to 14 with '<'
    l1, l2 = encode_mrz(f)
    p = decode_mrz(l1, l2)
    assert p["personal_number"].startswith("X1")
    assert len(p["personal_number"]) == 14
    assert set(p["personal_number"][2:]) <= {"<"}
    # check digit recomputes correctly
    assert fletcher4_check_digit(p["personal_number"]) == p["personal_number_cd"]

# ------------------------------
# Composite rebuild oracle check
# ------------------------------
def test_composite_recomputed_matches_reference_build():
    f = dict(BASE_FIELDS)
    l1, l2 = encode_mrz(f)
    p = decode_mrz(l1, l2)
    composite_src = (
        p["passport_number"] + p["passport_number_cd"] +
        p["birth_date"] + p["birth_date_cd"] +
        p["expiry_date"] + p["expiry_date_cd"] +
        p["personal_number"] + p["personal_number_cd"]
    )
    assert fletcher4_check_digit(composite_src) == p["composite_cd"]

# ------------------------------
# Randomized smoke over diverse data (catches COI/ROR around edge chars)
# ------------------------------
@pytest.mark.parametrize("surname,given,number,nat,sex", [
    ("O'BRIEN", "ANNE-MARIE", "Z9Y8X7W6V", "GBR", "F"),
    ("SMITH JR", "ALAN", "A1B2C3D4E", "CAN", "M"),
    ("LEE", "TAY LOR", "QWERTY123", "DE", "X"),
    ("NÚÑEZ", "JOSÉ", "000000001", "EUE", "<"),
    ("MÜLLER", "FRITZ-KARL", "12345678Z", "D", "x"),
])
def test_diverse_inputs_roundtrip_and_validate(surname, given, number, nat, sex):
    f = dict(BASE_FIELDS)
    f.update({
        "surname": surname,
        "given_names": given,
        "passport_number": number,
        "nationality": nat,
        "issuing_state": nat,
        "sex": sex,
    })
    l1, l2 = encode_mrz(f)
    out = validate_mrz(l1, l2)
    assert out["valid"] is True
    # sanity: decode returns 44/44 structure and non-empty composites
    p = out["fields"]
    assert len(p["passport_number"]) == 9
    assert p["composite_cd"].isdigit()
