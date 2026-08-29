from datetime import date
from typing import Any

from app.mrz import MrzResult


def evidence(rule_id: str, status: str, observed_value: Any, expected_condition: str, reason: str) -> dict[str, Any]:
    return {"rule_id": rule_id, "status": status, "observed_value": observed_value, "expected_condition": expected_condition, "reason": reason}


def validate_document(visible: dict[str, str], mrz: MrzResult) -> list[dict[str, Any]]:
    required = ("holder_name", "document_number", "nationality", "date_of_birth", "expiry_date")
    present = all(visible.get(field) for field in required)
    results = [evidence("fields.required", "PASS" if present else "FAIL", {field: visible.get(field) for field in required}, "all required visible fields present", "Required visible fields are present." if present else "One or more required visible fields are missing.")]
    try:
        dob, expiry = date.fromisoformat(visible["date_of_birth"]), date.fromisoformat(visible["expiry_date"])
        today = date.today()
        results += [
            evidence("date.birth.parse", "PASS", visible["date_of_birth"], "valid ISO date", "Date of birth parses."),
            evidence("date.expiry.parse", "PASS", visible["expiry_date"], "valid ISO date", "Expiry date parses."),
            evidence("date.expiry.after_birth", "PASS" if expiry > dob else "FAIL", {"dob": dob.isoformat(), "expiry": expiry.isoformat()}, "expiry after date of birth", "Expiry is after date of birth." if expiry > dob else "Expiry is not after date of birth."),
            evidence("date.birth.not_future", "PASS" if dob <= today else "FAIL", dob.isoformat(), "date of birth is not in the future", "Date of birth is not in the future." if dob <= today else "Date of birth is in the future."),
            evidence("date.expiry.current", "PASS" if expiry >= today else "FAIL", expiry.isoformat(), "expiry is today or later", "Credential is currently valid." if expiry >= today else "Credential is expired."),
        ]
    except (KeyError, ValueError):
        results.append(evidence("date.parse", "FAIL", {"dob": visible.get("date_of_birth"), "expiry": visible.get("expiry_date")}, "parseable calendar dates", "One or more document dates are missing or invalid."))
    if mrz.detected:
        results.extend(evidence(f"mrz.{name}", status, None, "individual MRZ check digit is valid", f"MRZ {name.replace('_', ' ')}.") for name, status in mrz.checks.items())
    else:
        results.append(evidence("mrz.detected", "UNAVAILABLE", None, "two valid MRZ lines detected", "MRZ could not be parsed."))
    return results

