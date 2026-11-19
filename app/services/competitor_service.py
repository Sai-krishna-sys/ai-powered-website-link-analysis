from typing import List
from app.schemas import CompetitorAnalysis, Competitor


class CompetitorService:
    def analyze(self, extracted) -> CompetitorAnalysis:
        text = getattr(extracted, "text", "") or getattr(extracted, "content", "")
        brand_name = getattr(extracted, "business_name", None) or "Unknown Brand"
        # No external search API configured: provide AI-suggested potential competitors only as placeholders.
        return CompetitorAnalysis(
            brand_name=brand_name,
            business_overview="Inferred from submitted website content.",
            main_business_category="Unknown",
            main_products_services=[],
            competitors_identified_from_sources=[],
            ai_suggested_potential_competitors=[],
            inferred_from_submitted_website=[text[:500]] if text else [],
            competitor_strengths=[],
            competitor_weaknesses=[],
            brand_competitive_advantages=[],
            market_positioning_opportunities=[],
        )


def analyze_competitors(extracted) -> CompetitorAnalysis:
    return CompetitorService().analyze(extracted)
