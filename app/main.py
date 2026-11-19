from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import AuthenticationError, RateLimitError, APIError
from app.services.analysis_service import AnalysisService
from app.schemas import LinkAnalysisResponse
from app.utils.validators import URLValidationError

app = FastAPI(title="AI Link Analysis API", version="1.0.0")

class LinkAnalysisRequest(BaseModel):
    url: str

@app.post("/link-analysis", response_model=LinkAnalysisResponse)
async def link_analysis(req: LinkAnalysisRequest):
    try:
        service = AnalysisService()
        result = await service.analyze_url(req.url)
        return result
    except URLValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="OpenAI authentication failed")
    except RateLimitError:
        raise HTTPException(status_code=429, detail="OpenAI rate limit exceeded")
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except APIError:
        raise HTTPException(status_code=502, detail="OpenAI service error")
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health():
    return {"status": "ok"}
