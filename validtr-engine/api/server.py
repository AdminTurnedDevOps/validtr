"""FastAPI server for the validtr engine."""

import logging

from fastapi import FastAPI

from api.routes.config import router as config_router
from api.routes.mcp import router as mcp_router
from api.routes.run import router as run_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="validtr engine",
    description="Python engine for validtr — agentic stack validation",
    version="0.1.0",
)

app.include_router(run_router, prefix="/api")
app.include_router(mcp_router, prefix="/api/mcp")
app.include_router(config_router, prefix="/api/config")


@app.get("/health")
async def health():
    return {"status": "ok"}
