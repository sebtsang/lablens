"""LabLens MCP HTTP server entry point.

Mounts the FastMCP streamable-HTTP app at the root, plus a `/health` endpoint
that Railway uses for healthchecks. Automatically loads `.env` on startup so
LABLENS_LLM_PROVIDER, GEMINI_API_KEY, etc. are available without manual export.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dotenv import load_dotenv

# Load .env before any module reads os.environ. override=False so explicit shell
# exports and Railway env vars take precedence.
load_dotenv(override=False)

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from lablens.mcp_instance import mcp  # noqa: E402


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    async with mcp.session_manager.run():
        yield


app = FastAPI(lifespan=lifespan, title="LabLens MCP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": "lablens"}


app.mount("/", mcp.streamable_http_app())
