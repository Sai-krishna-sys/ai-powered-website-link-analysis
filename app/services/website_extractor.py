import httpx
from bs4 import BeautifulSoup
from typing import List, Optional
from urllib.parse import urljoin, urlparse
from app.schemas import ExtractedWebsite
from app.utils.validators import validate_url

USER_AGENT = "Mozilla/5.0 (compatible; AILinkAnalysisBot/1.0)"
MAX_BYTES = 2 * 1024 * 1024
TIMEOUT = 20.0


def _clean_text(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines()]
    seen = set()
    out = []
    for ln in lines:
        if not ln:
            continue
        if ln in seen:
            continue
        seen.add(ln)
        out.append(ln)
    return "\n".join(out)


async def _fetch(url: str) -> bytes:
    safe_url = validate_url(url)
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml", "Accept-Encoding": "identity"}
    current = safe_url
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=False, verify=True) as client:
        for _ in range(5):
            validate_url(current)
            # try streaming interface first
            stream_cm = getattr(client, "stream", None)
            if stream_cm is not None:
                async with stream_cm("GET", current, headers=headers) as response:
                    if response.status_code in (301, 302, 303, 307, 308):
                        loc = response.headers.get("location")
                        if not loc:
                            break
                        current = urljoin(current, loc)
                        continue
                    if response.status_code >= 400:
                        raise RuntimeError(f"Website returned status {response.status_code}")
                    cl = response.headers.get("content-length")
                    if cl and int(cl) > MAX_BYTES:
                        raise RuntimeError("Response exceeds maximum allowed size")
                    total = 0
                    chunks = []
                    async for chunk in response.aiter_bytes():
                        total += len(chunk)
                        if total > MAX_BYTES:
                            raise RuntimeError("Response exceeds maximum allowed size")
                        chunks.append(chunk)
                    return b"".join(chunks)
            else:
                response = await client.get(current, headers=headers)
                if response.status_code in (301, 302, 303, 307, 308):
                    loc = response.headers.get("location")
                    if not loc:
                        break
                    current = urljoin(current, loc)
                    continue
                if response.status_code >= 400:
                    raise RuntimeError(f"Website returned status {response.status_code}")
                if len(response.content) > MAX_BYTES:
                    raise RuntimeError("Response exceeds maximum allowed size")
                return response.content
    raise RuntimeError("Too many redirects")


async def extract_website(url: str) -> ExtractedWebsite:
    content_bytes = await _fetch(url)
    safe_url = validate_url(url)
    try:
        html = content_bytes.decode("utf-8", errors="replace")
    except Exception:
        html = content_bytes.decode("latin-1", errors="replace")

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "noscript", "iframe"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else None
    meta_desc = None
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        meta_desc = meta["content"].strip()

    headings = [h.get_text(" ", strip=True) for h in soup.find_all(["h1", "h2", "h3"]) if h.get_text(strip=True)]

    business_name = None
    og_site = soup.find("meta", attrs={"property": "og:site_name"})
    if og_site and og_site.get("content"):
        business_name = og_site["content"].strip()
    elif title:
        business_name = title.split("|")[0].split("-")[0].strip() or None

    contact_info: List[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("mailto:") or href.startswith("tel:"):
            contact_info.append(href)

    location = None

    internal_links: List[str] = []
    base_host = urlparse(safe_url).hostname
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = urljoin(safe_url, href)
        if urlparse(full).hostname == base_host:
            internal_links.append(full)
    internal_links = list(dict.fromkeys(internal_links))[:50]

    products_services: List[str] = []
    for li in soup.find_all("li"):
        t = li.get_text(" ", strip=True)
        if 3 < len(t) < 120:
            products_services.append(t)
    products_services = list(dict.fromkeys(products_services))[:30]

    main_text = _clean_text(soup.get_text("\n", strip=True))
    if len(main_text.strip()) < 10:
        raise RuntimeError("Empty website content")

    return ExtractedWebsite(
        url=safe_url,
        title=title,
        meta_description=meta_desc,
        headings=headings,
        text=main_text[:12000],
        content=main_text[:12000],
        business_name=business_name,
        products_services=products_services,
        contact_info=contact_info,
        internal_links=internal_links,
        location=location,
    )


async def extract_content(url: str) -> ExtractedWebsite:
    return await extract_website(url)


async def fetch_website(url: str) -> ExtractedWebsite:
    return await extract_website(url)


async def extract_website_content(url: str) -> ExtractedWebsite:
    return await extract_website(url)
