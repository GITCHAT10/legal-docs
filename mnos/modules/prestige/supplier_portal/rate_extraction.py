import csv
import io
from typing import List, Dict, Any

class RateExtractionEngine:
    """
    Handles extraction from CSV/Excel rate sheets.
    """
    def extract_from_csv(self, csv_content: str) -> List[Dict[str, Any]]:
        f = io.StringIO(csv_content)
        reader = csv.DictReader(f)
        rates = []
        for row in reader:
            rates.append(row)
        return rates
