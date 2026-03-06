import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.middleware.safety_middleware import SafetyMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.base import engine, Base
    import app.db.models  # noqa: F401 — register all models
    from sqlalchemy import text

    async with engine.begin() as conn:
        # Create any tables that don't exist yet
        await conn.run_sync(Base.metadata.create_all)

        # Idempotently add columns introduced after the initial schema
        await conn.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(64)"
        ))
        await conn.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS salutation VARCHAR(16)"
        ))
        await conn.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_approved BOOLEAN NOT NULL DEFAULT false"
        ))
        await conn.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS pending_role_name VARCHAR(64)"
        ))
        # Unique index on username (IF NOT EXISTS is supported in PG 9.5+)
        await conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username) WHERE username IS NOT NULL"
        ))
        # Seed all roles (idempotent) — use individual inserts with bound params
        # to avoid SQLAlchemy misinterpreting JSON colons as bind parameters
        _roles = [
            ("admin",          "Full platform access",         '{"all":true}'),
            ("student",        "Basic query access",           '{"query":true}'),
            ("psychologist",   "Licensed psychologist access", '{"query":true,"upload":true,"edit_articles":true}'),
            ("rehab_staff",    "Rehabilitation staff access",  '{"query":true,"upload":true,"edit_articles":true}'),
            ("hospital_admin", "Hospital administrator access",'{"query":true,"upload":true,"edit_articles":true,"manage_kb":true}'),
        ]
        for _name, _desc, _perms in _roles:
            await conn.execute(
                text("INSERT INTO roles (id, name, description, permissions) VALUES (gen_random_uuid(), :name, :desc, CAST(:perms AS JSONB)) ON CONFLICT (name) DO NOTHING"),
                {"name": _name, "desc": _desc, "perms": _perms},
            )
    yield
    # Shutdown


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Safety pre-filter
    app.add_middleware(SafetyMiddleware)

    # Prometheus metrics
    Instrumentator().instrument(app).expose(app)

    # Routers
    from app.api.v1 import auth, query, knowledge_base, research, submissions, feedback, notifications, admin

    prefix = settings.API_V1_PREFIX

    app.include_router(auth.router, prefix=prefix)
    app.include_router(query.router, prefix=prefix)
    app.include_router(knowledge_base.router, prefix=prefix)
    app.include_router(research.router, prefix=prefix)
    app.include_router(submissions.router, prefix=prefix)
    app.include_router(feedback.router, prefix=prefix)
    app.include_router(notifications.router, prefix=prefix)
    app.include_router(admin.router, prefix=prefix)

    if settings.DEBUG:
        @app.exception_handler(Exception)
        async def debug_exception_handler(request: Request, exc: Exception):
            return JSONResponse(
                status_code=500,
                content={"detail": str(exc), "traceback": traceback.format_exc()},
            )

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": settings.APP_VERSION}

    return app


app = create_app()
