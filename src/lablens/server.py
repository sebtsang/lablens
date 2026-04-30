"""LabLens MCP HTTP server entry point.

Mounts the FastMCP streamable-HTTP app at the root, plus a `/health` endpoint
that Railway uses for healthchecks.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lablens.mcp_instance import mcp


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
