from dataclasses import dataclass

WEIGHTS = (7, 3, 1)
FILLER = "<"


def char_value(char: str) -> int:
    if char == FILLER:
        return 0
    if char.isdigit():
        return int(char)
    if "A" <= char <= "Z":
        return ord(char) - ord("A") + 10
    raise ValueError(f"unsupported MRZ character: {char!r}")


def check_digit(value: str) -> str:
    return str(sum(char_value(char) * WEIGHTS[index % 3] for index, char in enumerate(value)) % 10)


def normalize_line(line: str) -> str:
    return "".join(line.upper().split())


def decode_date(value: str) -> str:
    if len(value) != 6 or not value.isdigit():
        raise ValueError("MRZ date must be six digits")
    year = 2000 + int(value[:2]) if int(value[:2]) <= 39 else 1900 + int(value[:2])
    from datetime import date
    return date(year, int(value[2:4]), int(value[4:6])).isoformat()


@dataclass(frozen=True)
class MrzResult:
    detected: bool
    fields: dict[str, str]
    checks: dict[str, str]
    raw_lines: list[str]
    error: str | None = None


def _check(value: str, supplied: str) -> str:
    try:
        return "PASS" if supplied.isdigit() and check_digit(value) == supplied else "FAIL"
    except ValueError:
        return "FAIL"


def parse_mrz(raw_text: str) -> MrzResult:
    candidates = [normalize_line(line) for line in raw_text.splitlines() if len(normalize_line(line)) >= 30 and "<" in normalize_line(line)]
    if len(candidates) < 2:
        return MrzResult(False, {}, {}, [], "two MRZ lines not detected")
    line1, line2 = candidates[-2:]
    # OCR commonly drops one or two trailing filler glyphs from the name line.
    # Padding only this non-data suffix is deterministic MRZ format normalization.
    if line1.startswith("X<") and 40 <= len(line1) < 44:
        line1 = line1.ljust(44, FILLER)
    if len(line1) != 44 or len(line2) != 44:
        return MrzResult(False, {}, {}, [line1, line2], "MRZ lines must be exactly 44 characters")
    try:
        document_number = line2[0:9]
        dob_value, expiry_value = line2[13:19], line2[21:27]
        optional = line2[28:42]
        composite_value = line2[0:10] + line2[13:20] + line2[21:28] + line2[28:43]
        surname, given = line1[5:].split(FILLER + FILLER, 1)
        fields = {
            "document_type": line1[0], "issuing_state": line1[2:5],
            "surname": surname.replace(FILLER, " ").strip(), "given_names": given.replace(FILLER, " ").strip(),
            "document_number": document_number.rstrip(FILLER), "nationality": line2[10:13],
            "date_of_birth": decode_date(dob_value), "sex": line2[20], "expiry_date": decode_date(expiry_value),
            "optional_data": optional.rstrip(FILLER),
        }
        fields["holder_name"] = " ".join(part for part in (fields["given_names"], fields["surname"]) if part)
        checks = {
            "document_number_check": _check(document_number, line2[9]),
            "birth_date_check": _check(dob_value, line2[19]),
            "expiry_date_check": _check(expiry_value, line2[27]),
            "optional_data_check": _check(optional, line2[42]),
            "composite_check": _check(composite_value, line2[43]),
        }
        return MrzResult(True, fields, checks, [line1, line2])
    except (ValueError, IndexError) as error:
        return MrzResult(False, {}, {}, [line1, line2], str(error))
