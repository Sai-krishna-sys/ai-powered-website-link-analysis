from typing import List, Optional
from pydantic import BaseModel, Field


class Brand(BaseModel):
    name: str
    category: str
    summary: str


class Competitor(BaseModel):
    name: str
    source: str = "AI-suggested potential competitor"
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)


class CompetitorAnalysis(BaseModel):
    brand_name: str
    business_overview: str
    main_business_category: str
    main_products_services: List[str] = Field(default_factory=list)
    competitors_identified_from_sources: List[Competitor] = Field(default_factory=list)
    ai_suggested_potential_competitors: List[Competitor] = Field(default_factory=list)
    inferred_from_submitted_website: List[str] = Field(default_factory=list)
    competitor_strengths: List[str] = Field(default_factory=list)
    competitor_weaknesses: List[str] = Field(default_factory=list)
    brand_competitive_advantages: List[str] = Field(default_factory=list)
    market_positioning_opportunities: List[str] = Field(default_factory=list)


class TargetQuery(BaseModel):
    query: str
    platforms: List[str]
    search_intent: str
    business_relevance: str
    target_audience: str


class KeywordRecommendations(BaseModel):
    primary_keyword: str
    secondary_keywords: List[str] = Field(default_factory=list)
    long_tail_keywords: List[str] = Field(default_factory=list)
    relevant_business_keywords: List[str] = Field(default_factory=list)


class SeoTitle(BaseModel):
    recommended_title: str
    primary_keyword: str
    improved_title_structure: str


class MetaDescription(BaseModel):
    recommended_meta_description: str
    human_friendly_summary: str
    relevant_keywords: List[str] = Field(default_factory=list)


class SupportingContent(BaseModel):
    service_landing_pages: List[str] = Field(default_factory=list)
    industry_specific_pages: List[str] = Field(default_factory=list)
    faqs: List[str] = Field(default_factory=list)
    blog_topics: List[str] = Field(default_factory=list)
    location_specific_landing_pages: List[str] = Field(default_factory=list)
    supporting_business_articles: List[str] = Field(default_factory=list)


class SeoImprovements(BaseModel):
    keyword_recommendations: KeywordRecommendations
    seo_title: SeoTitle
    meta_description: MetaDescription
    supporting_content: SupportingContent


class TopService(BaseModel):
    service_name: str
    description: str
    target_industry: str
    target_customer: str
    main_benefit: str
    source_classification: str


class TargetAudience(BaseModel):
    primary_target_audience: str
    secondary_target_audience: str
    industry_segments: List[str] = Field(default_factory=list)
    business_types: List[str] = Field(default_factory=list)
    customer_profiles: List[str] = Field(default_factory=list)
    geographic_focus: Optional[str] = None
    customer_needs_challenges: List[str] = Field(default_factory=list)
    potential_customer_interests: List[str] = Field(default_factory=list)
    recommended_marketing_audience_segments: List[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    competitor_analysis: CompetitorAnalysis
    target_search_queries: List[TargetQuery]
    seo_improvements: SeoImprovements
    top_services: List[TopService]
    target_audience: TargetAudience


class LLMAnalysisOutput(BaseModel):
    brand: Brand
    analysis: AnalysisResult


class LinkAnalysisResponse(BaseModel):
    success: bool = True
    website: str
    brand: Brand
    analysis: AnalysisResult


class ExtractedWebsite(BaseModel):
    url: str
    title: Optional[str] = None
    meta_description: Optional[str] = None
    headings: List[str] = Field(default_factory=list)
    text: str = ""
    content: str = ""
    business_name: Optional[str] = None
    products_services: List[str] = Field(default_factory=list)
    contact_info: List[str] = Field(default_factory=list)
    internal_links: List[str] = Field(default_factory=list)
    location: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        if not self.content and self.text:
            self.content = self.text
        if not self.text and self.content:
            self.text = self.content
