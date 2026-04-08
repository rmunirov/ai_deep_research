"""FastAPI router with all research API endpoints."""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse

from deep_research.api.dependencies import (
    get_emitter_dep,
    get_research_service,
    get_settings_dep,
)
from deep_research.api.schemas import (
    ConfigResponse,
    ConfigUpdateRequest,
    ExportRequest,
    ExportResponse,
    ResearchCreateRequest,
    ResearchListItem,
    ResearchListResponse,
    ResearchResponse,
)
from deep_research.config import DepthPreset, Settings
from deep_research.schemas.research import ResearchCreate
from deep_research.services.event_emitter import EventEmitter
from deep_research.services.research_service import ResearchService

router = APIRouter(prefix="/api/v1", tags=["research"])


@router.post("/research", response_model=ResearchResponse)
async def create_research(
    body: ResearchCreateRequest,
    background_tasks: BackgroundTasks,
    service: ResearchService = Depends(get_research_service),
) -> Any:
    request = ResearchCreate(
        query=body.query,
        depth=DepthPreset(body.depth),
        interactive=body.interactive,
    )

    loop = asyncio.get_event_loop()
    future: asyncio.Future[Any] = loop.create_future()

    async def _run() -> None:
        try:
            result = await service.start_research(request)
            if not future.done():
                future.set_result(result)
        except Exception as exc:
            if not future.done():
                future.set_exception(exc)

    background_tasks.add_task(_run)

    # Return immediately with pending status
    from deep_research.db.engine import get_session
    from deep_research.db.repository import ResearchRepository

    await asyncio.sleep(0.5)  # Let the background task create the DB record

    async with get_session() as session:
        repo = ResearchRepository(session)
        researches = await repo.list_all(limit=1)
        if researches:
            r = researches[0]
            return ResearchResponse(
                id=r.id,
                query=r.query,
                status=r.status.value,
                depth=r.depth,
                artifacts_dir=r.artifacts_dir,
                config_snapshot=r.config_snapshot,
                started_at=r.started_at,
                completed_at=r.completed_at,
                error=r.error,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
    raise HTTPException(status_code=500, detail="Failed to create research")


@router.get("/research", response_model=ResearchListResponse)
async def list_researches(
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    service: ResearchService = Depends(get_research_service),
) -> Any:
    summaries = await service.list_researches(status=status, limit=limit, offset=offset)
    items = [
        ResearchListItem(
            id=s.id,
            query=s.query,
            status=s.status,
            depth=s.depth,
            created_at=s.created_at,
            completed_at=s.completed_at,
            total_cost_usd=s.total_cost_usd,
        )
        for s in summaries
    ]
    return ResearchListResponse(items=items, total=len(items))


@router.get("/research/{research_id}", response_model=ResearchResponse)
async def get_research(
    research_id: uuid.UUID,
    service: ResearchService = Depends(get_research_service),
) -> Any:
    try:
        return await service.get_detail(research_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/research/{research_id}/events")
async def research_events_sse(
    research_id: uuid.UUID,
    emitter: EventEmitter = Depends(get_emitter_dep),
) -> EventSourceResponse:
    async def _stream() -> AsyncIterator[dict[str, str]]:
        async for event in emitter.subscribe(research_id):
            yield {
                "event": event.event_type,
                "data": json.dumps(event.model_dump(mode="json"), default=str),
            }

    return EventSourceResponse(_stream())


@router.post("/research/{research_id}/resume", response_model=ResearchResponse)
async def resume_research(
    research_id: uuid.UUID,
    service: ResearchService = Depends(get_research_service),
) -> Any:
    try:
        return await service.resume_research(research_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/research/{research_id}/export", response_model=ExportResponse)
async def export_research(
    research_id: uuid.UUID,
    body: ExportRequest,
    service: ResearchService = Depends(get_research_service),
) -> Any:
    detail = await service.get_detail(research_id)
    if detail.artifacts_dir is None:
        raise HTTPException(status_code=400, detail="No artifacts directory")

    from deep_research.tools.export_tool import export_report

    output_path = export_report(detail.artifacts_dir, body.format)
    return ExportResponse(path=output_path, format=body.format)


@router.get("/config", response_model=ConfigResponse)
async def get_config(
    settings: Settings = Depends(get_settings_dep),
) -> Any:
    return ConfigResponse(
        default_model=settings.default_model,
        language=settings.language,
        researches_dir=str(settings.researches_dir),
        api_host=settings.api_host,
        api_port=settings.api_port,
        max_search_results=settings.max_search_results,
    )


@router.put("/config", response_model=ConfigResponse)
async def update_config(
    body: ConfigUpdateRequest,
    settings: Settings = Depends(get_settings_dep),
) -> Any:
    if body.default_model is not None:
        settings.default_model = body.default_model
    if body.language is not None:
        settings.language = body.language
    if body.max_search_results is not None:
        settings.max_search_results = body.max_search_results
    return ConfigResponse(
        default_model=settings.default_model,
        language=settings.language,
        researches_dir=str(settings.researches_dir),
        api_host=settings.api_host,
        api_port=settings.api_port,
        max_search_results=settings.max_search_results,
    )
