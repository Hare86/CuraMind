"""
Research agent — runs twice per week.
Searches PubMed + Google Scholar, scrapes articles, generates summaries,
adds to admin review queue, and sends admin notifications.
"""
import asyncio

from app.workers.celery_app import celery_app

PSYCHOLOGY_SEARCH_TERMS = [
    "cognitive behavioral therapy",
    "DSM-5 clinical psychology",
    "depression treatment efficacy",
    "anxiety disorder interventions",
    "trauma PTSD treatment",
    "psychological rehabilitation",
    "psychotherapy outcomes",
    "neuropsychology disorders",
]


@celery_app.task(name="app.workers.research_worker.run_research_agent")
def run_research_agent() -> dict:
    """
    Scheduled task: searches multiple sources, collects new articles,
    summarizes them, and queues for admin review.
    """
    return asyncio.get_event_loop().run_until_complete(_run_agent())


async def _run_agent() -> dict:
    from app.core.config import settings
    from app.db.base import AsyncSessionLocal

    articles_found = 0
    articles_stored = 0

    async with AsyncSessionLocal() as db:
        for search_term in PSYCHOLOGY_SEARCH_TERMS:
            # Search PubMed
            pubmed_articles = await _search_pubmed(search_term)
            for article in pubmed_articles:
                stored = await _store_article_if_new(db, article)
                if stored:
                    articles_stored += 1
                articles_found += 1

        await db.commit()

        # Notify all admins
        if articles_stored > 0:
            await _notify_admins(db, articles_stored)
            await db.commit()

    return {"articles_found": articles_found, "articles_stored": articles_stored}


async def _search_pubmed(search_term: str) -> list[dict]:
    """Search PubMed E-utilities API for recent psychology papers."""
    import httpx
    from app.core.config import settings

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    params = {
        "db": "pubmed",
        "term": f"{search_term}[Title/Abstract]",
        "retmax": 5,
        "sort": "date",
        "retmode": "json",
        "api_key": settings.PUBMED_API_KEY,
        "email": settings.PUBMED_EMAIL,
    }

    articles = []
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Search for IDs
            search_resp = await client.get(f"{BASE_URL}/esearch.fcgi", params=params)
            ids = search_resp.json().get("esearchresult", {}).get("idlist", [])

            if not ids:
                return []

            # Fetch summaries
            fetch_resp = await client.get(
                f"{BASE_URL}/esummary.fcgi",
                params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
            )
            result = fetch_resp.json().get("result", {})

            for pmid in ids:
                item = result.get(pmid, {})
                title = item.get("title", "")
                if not title:
                    continue

                url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                authors = ", ".join(
                    a.get("name", "") for a in item.get("authors", [])[:3]
                )

                articles.append(
                    {
                        "title": title,
                        "url": url,
                        "source": "pubmed",
                        "authors": authors,
                        "abstract": item.get("source", ""),
                    }
                )
    except Exception:
        pass

    return articles


async def _store_article_if_new(db, article_data: dict) -> bool:
    """Store article in DB if URL not already present. Returns True if new."""
    from sqlalchemy import select
    from app.db.models.research_article import ResearchArticle

    existing = await db.execute(
        select(ResearchArticle).where(ResearchArticle.url == article_data["url"])
    )
    if existing.scalar_one_or_none():
        return False

    summary = await _generate_summary(article_data.get("abstract") or article_data["title"])

    article = ResearchArticle(
        title=article_data["title"],
        url=article_data["url"],
        source=article_data.get("source", "pubmed"),
        authors=article_data.get("authors"),
        abstract=article_data.get("abstract"),
        summary=summary,
        status="pending_review",
    )
    db.add(article)
    return True


async def _generate_summary(text: str) -> str | None:
    """Use Mistral via Ollama to generate a brief summary."""
    import httpx
    from app.core.config import settings

    prompt = (
        f"Summarize this psychology research paper abstract in 2-3 sentences "
        f"for a clinical/academic audience:\n\n{text[:1000]}"
    )
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.MISTRAL_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": 200, "temperature": 0.3},
                },
            )
            return response.json().get("response", "").strip() or None
    except Exception:
        return None


async def _notify_admins(db, article_count: int) -> None:
    """Create notification records for all admin users."""
    from sqlalchemy import select, join
    from app.db.models.user import User
    from app.db.models.role import Role
    from app.db.models.notification import Notification

    result = await db.execute(
        select(User).join(Role, User.role_id == Role.id).where(Role.name == "admin")
    )
    admins = result.scalars().all()

    for admin in admins:
        notification = Notification(
            user_id=admin.id,
            message=(
                f"Research agent found {article_count} new psychology paper(s) "
                f"awaiting your review."
            ),
            notification_type="research_found",
        )
        db.add(notification)
