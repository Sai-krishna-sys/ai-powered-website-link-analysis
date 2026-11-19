from app.services.website_extractor import extract_website
from app.services.llm_service import LLMService
from app.schemas import LinkAnalysisResponse


class AnalysisService:
    async def analyze_url(self, url: str) -> LinkAnalysisResponse:
        from app.utils.validators import validate_url
        safe_url = validate_url(url)
        extracted = await extract_website(safe_url)
        llm = LLMService()
        result = await llm.analyze(extracted, safe_url)
        # enforce exactly 5
        if len(result.analysis.target_search_queries) != 5:
            result.analysis.target_search_queries = result.analysis.target_search_queries[:5]
        if len(result.analysis.top_services) != 5:
            result.analysis.top_services = result.analysis.top_services[:5]
        return LinkAnalysisResponse(
            success=True,
            website=safe_url,
            brand=result.brand,
            analysis=result.analysis,
        )


async def analyze_link(url: str) -> LinkAnalysisResponse:
    return await AnalysisService().analyze_url(url)
