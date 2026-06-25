"""FastAPI application entry point."""

import logging
from asyncio import get_running_loop
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.db.graph_repository import GraphRepository
from app.exceptions import AppException, EmptyTextError, NlpProcessingError, Neo4jConnectionError
from app.nlp.pipeline import process_text

import logging
import os
from pathlib import Path

# Создаём директорию для логов, если её нет
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Настраиваем корневой логгер
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),                     # консоль
        logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8"),  # файл
    ],
)
logger = logging.getLogger(__name__)

repo: GraphRepository | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global repo
    repo = GraphRepository(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
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

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # или ["*"] для теста
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


class ExtractRequest(BaseModel):
    text: str

class RecommendResponse(BaseModel):
    recommendations: list[dict]

class ExtractResponse(BaseModel):
    entities: list[dict]
    relations: list[dict]
    graph_id: str


@app.post("/extract", response_model=ExtractResponse)
async def extract(request: ExtractRequest):
    if not request.text.strip():
        raise EmptyTextError()

    try:
        loop = get_running_loop()
        result = await loop.run_in_executor(None, process_text, request.text)
    except Exception as exc:
        logger.exception("NLP processing failed")
        raise NlpProcessingError(str(exc))

    try:
        graph_id = await repo.save_graph(result["entities"], result["relations"])
    except Exception as exc:
        logger.exception("Failed to save graph to Neo4j")
        raise Neo4jConnectionError(str(exc))

    return ExtractResponse(
        entities=result["entities"],
        relations=result["relations"],
        graph_id=graph_id,
    )
    
class RecommendResponse(BaseModel):
    recommendations: list[dict]


@app.get("/recommend", response_model=RecommendResponse)
async def recommend(entity_id: str):
    try:
        recs = await repo.recommend_similar_persons(entity_id)
    except Exception as exc:
        logger.exception("Failed to get recommendations")
        raise Neo4jConnectionError(str(exc))

    return RecommendResponse(recommendations=recs)