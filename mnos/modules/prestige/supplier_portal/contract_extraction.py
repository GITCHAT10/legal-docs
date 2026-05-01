import uuid
from typing import Dict, List, Any, Optional
from mnos.modules.prestige.supplier_portal.models import ContractExtractionResult, ExtractedRoomRate, ExtractedMealPlanRule, ExtractedTransferRule

class ContractExtractionEngine:
    """
    Mock engine for extracting structured data from supplier contract PDFs.
    Doctrine: AI output remains DRAFT until supplier confirmed.
    """
    def extract_from_pdf(self, filename: str) -> ContractExtractionResult:
        # In a real system, this would use OCR/LLM for extraction.
        # For the pilot, we simulate based on the filename or default mock data.

        resort_name = filename.split("_")[0] if "_" in filename else "Unknown Resort"

        result = ContractExtractionResult(
            resort_name=resort_name,
            effective_period={"start": "2024-01-01", "end": "2024-12-31"},
            room_rates=[
                ExtractedRoomRate(
                    category_code="BEACH_VILLA",
                    category_name="Beach Villa",
                    season_name="Winter Peak",
                    start_date="2024-01-01",
                    end_date="2024-04-30",
                    sgl_rate=500.0,
                    dbl_rate=500.0,
                    trpl_rate=650.0,
                    quad_rate=800.0,
                    extra_adult_rate=150.0,
                    child_rate=75.0
                )
            ],
            meal_plans=[
                ExtractedMealPlanRule(plan_code="HB", adult_supplement=80.0, child_supplement=40.0),
                ExtractedMealPlanRule(plan_code="FB", adult_supplement=150.0, child_supplement=75.0)
            ],
            transfers=[
                ExtractedTransferRule(
                    transfer_type="SEAPLANE",
                    adult_rate=450.0,
                    child_rate=225.0,
                    baggage_allowance_kg=20.0,
                    excess_baggage_rate=5.0
                )
            ],
            status="AI_EXTRACTED_DRAFT"
        )
        return result
