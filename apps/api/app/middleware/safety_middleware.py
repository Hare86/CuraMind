"""
Safety middleware — inspects incoming requests to query endpoints.
Provides a second defensive layer before route handlers are called.
"""
import json

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

QUERY_PATHS = {"/api/query", "/api/generate-mcq", "/api/generate-case"}

HARD_BLOCK_PATTERNS = [
    "prescribe",
    "medication dosage",
    "what drugs should i take",
    "diagnose me",
    "am i crazy",
    "am i mentally ill",
    "kill myself",
    "suicide",
    "self harm",
    "self-harm",
    "hurt myself",
]


class SafetyMiddleware(BaseHTTPMiddleware):
    """
    Fast pattern-based pre-filter for obviously blocked content.
    This runs BEFORE the Safety Service (Mistral) for zero-latency hard blocks.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path not in QUERY_PATHS or request.method != "POST":
            return await call_next(request)

        try:
            body_bytes = await request.body()
            body = json.loads(body_bytes)
            query_text = (body.get("query") or body.get("topic") or "").lower()

            for pattern in HARD_BLOCK_PATTERNS:
                if pattern in query_text:
                    return JSONResponse(
                        status_code=200,
                        content={
                            "answer": (
                                "This system is for educational purposes only. "
                                "Please consult a licensed mental health professional."
                            ),
                            "citations": [],
                            "was_blocked": True,
                        },
                    )
        except Exception:
            pass

        # Re-attach body so route handler can read it
        async def receive():
            return {"type": "http.request", "body": body_bytes}

        request._receive = receive
        return await call_next(request)
