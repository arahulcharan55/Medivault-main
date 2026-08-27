"""Pattern-based extraction of facts explicitly stated in medical documents.

This is not a diagnostic model. It only captures labeled values that appear in
the source text (lab lines, vitals, prescriptions, diagnoses, procedures).
"""

from __future__ import annotations

import re
from typing import Any

LAB_PATTERNS: list[tuple[str, str, str | None, str | None]] = [
    # display, regex (value capture group 1, optional unit group 2), default unit, loinc-like code
    ("HbA1c", r"HbA1c\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(%|percent)?", "%", "4548-4"),
    ("Hemoglobin", r"(?:Hemoglobin|Hb)(?!\s*A1c)\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(g/dL|g/dl|gm%)?", "g/dL", "718-7"),
    ("WBC", r"WBC\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(x?10\^?3/?[µu]?L|cells/µL)?", "10^3/µL", "6690-2"),
    ("RBC", r"RBC\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(x?10\^?6/?[µu]?L)?", "10^6/µL", "789-8"),
    ("Glucose", r"(?:Fasting\s+)?Glucose\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(mg/dL|mg/dl|mmol/L)?", "mg/dL", "2345-7"),
    ("Creatinine", r"Creatinine\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(mg/dL|mg/dl)?", "mg/dL", "2160-0"),
    ("TSH", r"TSH\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(mIU/L|µIU/mL|uIU/mL)?", "mIU/L", "3016-3"),
    ("Cholesterol", r"(?:Total\s+)?Cholesterol\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(mg/dL|mg/dl)?", "mg/dL", "2093-3"),
    ("HDL", r"HDL(?:\s*Cholesterol)?\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(mg/dL|mg/dl)?", "mg/dL", "2085-9"),
    ("LDL", r"LDL(?:\s*Cholesterol)?\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(mg/dL|mg/dl)?", "mg/dL", "2089-1"),
    ("Triglycerides", r"Triglycerides?\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(mg/dL|mg/dl)?", "mg/dL", "2571-8"),
    ("Platelets", r"Platelets?\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(x?10\^?3/?[µu]?L)?", "10^3/µL", "777-3"),
]

REFERENCE_RANGES: dict[str, tuple[float | None, float | None]] = {
    "HbA1c": (None, 5.7),
    "Hemoglobin": (12.0, 17.5),
    "Glucose": (70.0, 99.0),
    "Creatinine": (0.6, 1.3),
    "TSH": (0.4, 4.0),
    "Cholesterol": (None, 200.0),
    "HDL": (40.0, None),
    "LDL": (None, 100.0),
    "Triglycerides": (None, 150.0),
    "WBC": (4.0, 11.0),
}


def _flag(name: str, value: str) -> str | None:
    try:
        numeric = float(re.sub(r"[^0-9.]", "", value.split()[0]))
    except (ValueError, IndexError):
        return None
    bounds = REFERENCE_RANGES.get(name)
    if not bounds:
        return None
    low, high = bounds
    if low is not None and numeric < low:
        return "low"
    if high is not None and numeric > high:
        return "high"
    return "normal"


def mock_structured_extraction(text: str) -> dict[str, Any]:
    """Extract explicitly pattern-matched facts only. No inference."""
    result: dict[str, Any] = {
        "document_date": None,
        "hospital": None,
        "physician": None,
        "diagnoses": [],
        "medications": [],
        "vitals": [],
        "laboratory_results": [],
        "procedures": [],
        "allergies": [],
        "source_text_references": [],
        "confidence": 0.0,
    }

    date_match = re.search(
        r"(?:Date|Dated|Report Date|Collected)\s*[:\-]?\s*(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})",
        text,
        re.I,
    )
    if date_match:
        result["document_date"] = date_match.group(1)
        result["source_text_references"].append(date_match.group(0).strip())

    hospital_match = re.search(
        r"(?:Hospital|Clinic|Medical Center|Laboratory)\s*[:\-]?\s*([A-Za-z0-9 .,&'-]{3,80})",
        text,
        re.I,
    )
    if hospital_match:
        result["hospital"] = hospital_match.group(1).strip()
        result["source_text_references"].append(hospital_match.group(0).strip())

    physician_match = re.search(r"(?:Dr\.|Doctor|Physician)\s*([A-Za-z .]{3,60})", text, re.I)
    if physician_match:
        result["physician"] = physician_match.group(1).strip()
        result["source_text_references"].append(physician_match.group(0).strip())

    for diag in re.findall(r"(?:Diagnosis|Impression|Dx)\s*[:\-]?\s*([^\n\r]{3,120})", text, re.I):
        result["diagnoses"].append({"display_name": diag.strip(), "source": diag.strip()})

    for raw_med in re.findall(r"(?:Rx|Prescription|Medication)\s*[:\-]?\s*([^\n\r]{3,160})", text, re.I):
        med = _parse_medication(raw_med.strip())
        result["medications"].append(med)

    bp = re.search(
        r"(?:BP|Blood Pressure)\s*[:\-]?\s*([0-9]{2,3}\s*/\s*[0-9]{2,3})(?:\s*(mmHg))?",
        text,
        re.I,
    )
    if bp:
        unit = bp.group(2) or "mmHg"
        result["vitals"].append(
            {
                "display_name": "Blood Pressure",
                "value": bp.group(1).replace(" ", ""),
                "unit": unit,
                "code": "85354-9",
                "source": bp.group(0).strip(),
            }
        )

    hr = re.search(r"(?:HR|Heart Rate|Pulse)\s*[:\-]?\s*([0-9]{2,3})\s*(bpm|beats/min)?", text, re.I)
    if hr:
        result["vitals"].append(
            {
                "display_name": "Heart Rate",
                "value": hr.group(1),
                "unit": hr.group(2) or "bpm",
                "code": "8867-4",
                "source": hr.group(0).strip(),
            }
        )

    temp = re.search(r"(?:Temp(?:erature)?)\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(°?F|°?C)?", text, re.I)
    if temp:
        result["vitals"].append(
            {
                "display_name": "Temperature",
                "value": temp.group(1),
                "unit": temp.group(2) or "°C",
                "code": "8310-5",
                "source": temp.group(0).strip(),
            }
        )

    spo2 = re.search(r"(?:SpO2|Oxygen Saturation)\s*[:\-]?\s*([0-9]{2,3})\s*%?", text, re.I)
    if spo2:
        result["vitals"].append(
            {
                "display_name": "SpO2",
                "value": spo2.group(1),
                "unit": "%",
                "code": "2708-6",
                "source": spo2.group(0).strip(),
            }
        )

    seen_labs: set[str] = set()
    for display, pattern, default_unit, code in LAB_PATTERNS:
        match = re.search(pattern, text, re.I)
        if not match:
            continue
        if display in seen_labs:
            continue
        seen_labs.add(display)
        value = match.group(1)
        unit = (match.group(2) if match.lastindex and match.lastindex >= 2 else None) or default_unit
        flag = _flag(display, value)
        result["laboratory_results"].append(
            {
                "display_name": display,
                "value": value,
                "unit": unit,
                "code": code,
                "interpretation": flag,
                "source": match.group(0).strip(),
            }
        )

    for proc in re.findall(r"(?:Procedure|Surgery|Investigation)\s*[:\-]?\s*([^\n\r]{3,120})", text, re.I):
        result["procedures"].append({"display_name": proc.strip(), "source": proc.strip()})

    for allergy in re.findall(r"(?:Allergy|Allergic to|Allergies)\s*[:\-]?\s*([^\n\r]{3,80})", text, re.I):
        result["allergies"].append({"display_name": allergy.strip(), "source": allergy.strip()})

    result["confidence"] = _confidence(result)
    return result


def _parse_medication(raw: str) -> dict[str, Any]:
    dose = re.search(r"(\d+\s*(?:mg|mcg|g|ml|IU|units))", raw, re.I)
    freq = re.search(
        r"(once daily|twice daily|thrice daily|three times daily|bid|tid|od|hs|qhs|every \d+ hours?)",
        raw,
        re.I,
    )
    name = raw
    if dose:
        name = raw[: dose.start()].strip(" -,") or raw.split()[0]
    return {
        "medication_name": name.strip(),
        "dosage": dose.group(1).replace(" ", "") if dose else None,
        "frequency": freq.group(1) if freq else None,
        "instructions": raw,
        "source": raw,
    }


def _confidence(data: dict[str, Any]) -> float:
    score = 0.35
    if data.get("document_date"):
        score += 0.08
    if data.get("hospital"):
        score += 0.05
    if data.get("physician"):
        score += 0.05
    for key, weight in (
        ("diagnoses", 0.12),
        ("medications", 0.12),
        ("vitals", 0.1),
        ("laboratory_results", 0.12),
        ("procedures", 0.06),
        ("allergies", 0.05),
    ):
        if data.get(key):
            score += weight
    return round(min(score, 0.95), 2)


def validate_extraction_schema(data: dict) -> dict:
    required_keys = {
        "document_date",
        "hospital",
        "physician",
        "diagnoses",
        "medications",
        "vitals",
        "laboratory_results",
        "procedures",
        "allergies",
        "source_text_references",
    }
    if not required_keys.issubset(data.keys()):
        raise ValueError("Extraction schema validation failed")
    for key in [
        "diagnoses",
        "medications",
        "vitals",
        "laboratory_results",
        "procedures",
        "allergies",
        "source_text_references",
    ]:
        if not isinstance(data[key], list):
            raise ValueError(f"Invalid type for {key}")
    return data


def has_extracted_facts(data: dict) -> bool:
    return any(
        data.get(key)
        for key in ("diagnoses", "medications", "vitals", "laboratory_results", "procedures", "allergies")
    )
