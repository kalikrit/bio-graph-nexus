"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
from app.db.graph_repository import GraphRepository
from app.nlp.pipeline import process_text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Глобальный репозиторий
repo: GraphRepository | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global repo
    repo = GraphRepository(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    try:
        await repo.init_constraints()
        logger.info("Connected to Neo4j")
    except Exception:
        logger.exception("Failed to initialize Neo4j constraints")
        raise
    yield
    if repo:
        await repo.close()
        logger.info("Neo4j connection closed")


app = FastAPI(title="BioGraph Nexus API", version="0.1.0", lifespan=lifespan)


class ExtractRequest(BaseModel):
    text: str


class ExtractResponse(BaseModel):
    entities: list[dict]
    relations: list[dict]
    graph_id: str


@app.post("/extract", response_model=ExtractResponse)
async def extract(request: ExtractRequest):
    if not request.text.strip():
        raise HTTPException(status_code=422, detail="Text must not be empty")

    try:
        from asyncio import get_running_loop
        loop = get_running_loop()
        result = await loop.run_in_executor(None, process_text, request.text)
    except Exception:
        logger.exception("NLP processing failed")
        raise HTTPException(status_code=500, detail="NLP processing error")

    try:
        graph_id = await repo.save_graph(result["entities"], result["relations"])
    except Exception:
        logger.exception("Failed to save graph to Neo4j")
        raise HTTPException(status_code=500, detail="Database error")

    return ExtractResponse(
        entities=result["entities"],
        relations=result["relations"],
        graph_id=graph_id,
    )