import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.utils.validators import validate_url, URLValidationError
from app.schemas import LLMAnalysisOutput, Brand, AnalysisResult, CompetitorAnalysis, TargetQuery, SeoImprovements, KeywordRecommendations, SeoTitle, MetaDescription, SupportingContent, TopService, TargetAudience, LinkAnalysisResponse


def test_valid_url():
    assert validate_url("https://example.com") == "https://example.com"


def test_invalid_url():
    with pytest.raises(URLValidationError):
        validate_url("ftp://example.com")
    with pytest.raises(URLValidationError):
        validate_url("not-a-url")


def test_private_ip():
    with pytest.raises(URLValidationError):
        validate_url("http://192.168.1.1")


def test_localhost():
    with pytest.raises(URLValidationError):
        validate_url("http://localhost:8000")
    with pytest.raises(URLValidationError):
        validate_url("http://127.0.0.1")


def test_ssrf_variants():
    for u in ["http://10.0.0.1", "http://172.16.0.1", "http://169.254.169.254"]:
        with pytest.raises(URLValidationError):
            validate_url(u)


def sample_llm_output():
    return LLMAnalysisOutput(
        brand=Brand(name="Example", category="Tech", summary="Summary"),
        analysis=AnalysisResult(
            competitor_analysis=CompetitorAnalysis(
                brand_name="Example", business_overview="ov", main_business_category="cat",
                main_products_services=["svc"],
                ai_suggested_potential_competitors=[],
            ),
            target_search_queries=[TargetQuery(query=f"q{i}", platforms=["Google"], search_intent="intent", business_relevance="rel", target_audience="aud") for i in range(5)],
            seo_improvements=SeoImprovements(
                keyword_recommendations=KeywordRecommendations(primary_keyword="pk"),
                seo_title=SeoTitle(recommended_title="t", primary_keyword="pk", improved_title_structure="s"),
                meta_description=MetaDescription(recommended_meta_description="m", human_friendly_summary="h"),
                supporting_content=SupportingContent(),
            ),
            top_services=[TopService(service_name=f"s{i}", description="d", target_industry="i", target_customer="c", main_benefit="b", source_classification="actual website content") for i in range(5)],
            target_audience=TargetAudience(primary_target_audience="p", secondary_target_audience="s"),
        ),
    )


@pytest.mark.asyncio
async def test_openai_parsing():
    from app.services.llm_service import LLMService
    fake_resp = MagicMock()
    fake_resp.choices = [MagicMock(message=MagicMock(parsed=sample_llm_output()))]
    fake_resp.usage = MagicMock(prompt_tokens=10, completion_tokens=20)
    with patch("app.services.llm_service.AsyncOpenAI") as mock_client:
        instance = mock_client.return_value
        instance.beta.chat.completions.parse = AsyncMock(return_value=fake_resp)
        svc = LLMService()
        out = await svc.analyze(MagicMock(text="hello", content="hello"), "https://example.com")
        assert out.brand.name == "Example"


@pytest.mark.asyncio
async def test_invalid_llm_response():
    from app.services.llm_service import LLMService
    fake_resp = MagicMock()
    fake_resp.choices = [MagicMock(message=MagicMock(parsed=None))]
    with patch("app.services.llm_service.AsyncOpenAI") as mock_client:
        instance = mock_client.return_value
        instance.beta.chat.completions.parse = AsyncMock(return_value=fake_resp)
        svc = LLMService()
        with pytest.raises(ValueError):
            await svc.analyze(MagicMock(text="hello", content="hello"), "https://example.com")


@pytest.mark.asyncio
async def test_website_extraction():
    fake_html = "<html><head><title>Example</title><meta name='description' content='desc'></head><body><h1>Hi</h1><p>Hello world content here</p></body></html>"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}
    async def aiter_bytes():
        yield fake_html.encode()
    mock_response.aiter_bytes = aiter_bytes
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=mock_response)
    cm.__aexit__ = AsyncMock(return_value=None)
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.stream = MagicMock(return_value=cm)
    with patch("app.services.website_extractor.httpx.AsyncClient", return_value=mock_client):
        from app.services.website_extractor import extract_website
        extracted = await extract_website("https://example.com")
        assert extracted.title == "Example"
        assert "Hello world" in extracted.text


@pytest.mark.asyncio
async def test_missing_website_content():
    fake_html = "<html><head><title>Example</title></head><body><script>x</script></body></html>"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}
    async def aiter_bytes():
        yield fake_html.encode()
    mock_response.aiter_bytes = aiter_bytes
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=mock_response)
    cm.__aexit__ = AsyncMock(return_value=None)
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.stream = MagicMock(return_value=cm)
    with patch("app.services.website_extractor.httpx.AsyncClient", return_value=mock_client):
        from app.services.website_extractor import extract_website
        with pytest.raises(RuntimeError):
            await extract_website("https://example.com")


@pytest.mark.asyncio
async def test_website_timeout():
    import httpx
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
    cm.__aexit__ = AsyncMock(return_value=None)
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.stream = MagicMock(return_value=cm)
    with patch("app.services.website_extractor.httpx.AsyncClient", return_value=mock_client):
        from app.services.website_extractor import extract_website
        with pytest.raises(Exception):
            await extract_website("https://example.com")


@pytest.mark.asyncio
async def test_oversized_stream():
    big = b"x" * (2 * 1024 * 1024 + 10)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}
    async def aiter_bytes():
        yield big
    mock_response.aiter_bytes = aiter_bytes
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=mock_response)
    cm.__aexit__ = AsyncMock(return_value=None)
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.stream = MagicMock(return_value=cm)
    with patch("app.services.website_extractor.httpx.AsyncClient", return_value=mock_client):
        from app.services.website_extractor import extract_website
        with pytest.raises(RuntimeError):
            await extract_website("https://example.com")


@pytest.mark.asyncio
async def test_redirect_validation():
    # redirect to private IP should be rejected
    mock_response = MagicMock()
    mock_response.status_code = 302
    mock_response.headers = {"location": "http://127.0.0.1/secret"}
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=mock_response)
    cm.__aexit__ = AsyncMock(return_value=None)
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.stream = MagicMock(return_value=cm)
    with patch("app.services.website_extractor.httpx.AsyncClient", return_value=mock_client):
        from app.services.website_extractor import extract_website
        with pytest.raises(URLValidationError):
            await extract_website("https://example.com")


@pytest.mark.asyncio
async def test_api_success():
    from fastapi.testclient import TestClient
    import app.main as main_module
    canned = LinkAnalysisResponse(
        success=True,
        website="https://example.com",
        brand=sample_llm_output().brand,
        analysis=sample_llm_output().analysis,
    )
    with patch("app.main.AnalysisService") as mock_svc_cls:
        instance = mock_svc_cls.return_value
        instance.analyze_url = AsyncMock(return_value=canned)
        client = TestClient(main_module.app)
        resp = client.post("/link-analysis", json={"url": "https://example.com"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["analysis"]["target_search_queries"]) == 5
        assert len(data["analysis"]["top_services"]) == 5


@pytest.mark.asyncio
async def test_api_error_handling():
    from fastapi.testclient import TestClient
    import app.main as main_module
    with patch("app.main.AnalysisService") as mock_svc_cls:
        instance = mock_svc_cls.return_value
        instance.analyze_url = AsyncMock(side_effect=URLValidationError("bad"))
        client = TestClient(main_module.app)
        resp = client.post("/link-analysis", json={"url": "https://example.com"})
        assert resp.status_code == 400


def test_all_five_sections():
    out = sample_llm_output()
    a = out.analysis
    assert a.competitor_analysis is not None
    assert len(a.target_search_queries) == 5
    assert a.seo_improvements is not None
    assert len(a.top_services) == 5
    assert a.target_audience is not None


def test_competitor_labeling():
    out = sample_llm_output()
    ca = out.analysis.competitor_analysis
    assert hasattr(ca, "ai_suggested_potential_competitors")
    assert hasattr(ca, "competitors_identified_from_sources")
