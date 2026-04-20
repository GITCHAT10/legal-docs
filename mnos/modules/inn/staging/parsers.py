import pandas as pd
import io
from typing import List, Dict, Tuple
from .models import StagingStatus
from datetime import datetime

def validate_row(row: Dict) -> List[str]:
    errors = []
    if not row.get("guest_name"):
        errors.append("guest_name is required")

    try:
        cin = row.get("check_in")
        cout = row.get("check_out")
        if not cin or not cout:
            errors.append("Both check_in and check_out are required")
        else:
            if cout <= cin:
                errors.append("check_out must be after check_in")
    except Exception:
        errors.append("Invalid date format")

    occupancy = row.get("occupancy", 0)
    if occupancy is not None and occupancy < 0:
        errors.append("occupancy cannot be negative")

    total_amount = row.get("total_amount", 0)
    if total_amount is not None and total_amount < 0:
        errors.append("total_amount cannot be negative")

    return errors

def parse_xlsx(file_content: bytes, mapping: Dict) -> List[Dict]:
    df = pd.read_excel(io.BytesIO(file_content))
    results = []
    for index, row in df.iterrows():
        # Mapping Stage
        entry = {
            "row_number": index + 2, # Excel rows start at 1, header is 1
            "guest_name": row.get(mapping.get("guest_name_col")),
            "check_in": row.get(mapping.get("in_col")),
            "check_out": row.get(mapping.get("out_col")),
            "room_type": row.get(mapping.get("room_col")),
            "occupancy": row.get(mapping.get("occupancy_col"), 1),
            "total_amount": row.get(mapping.get("price_col"), 0.0),
            "currency": str(row.get(mapping.get("currency_col"), "USD")).upper()
        }

        # Data conversion logic
        try:
            if isinstance(entry["check_in"], str):
                entry["check_in"] = pd.to_datetime(entry["check_in"]).to_pydatetime()
            if isinstance(entry["check_out"], str):
                entry["check_out"] = pd.to_datetime(entry["check_out"]).to_pydatetime()
        except Exception:
            pass # Validation will catch invalid types

        entry["validation_errors"] = validate_row(entry)
        entry["parser_stage"] = "STAGING"
        results.append(entry)
    return results
