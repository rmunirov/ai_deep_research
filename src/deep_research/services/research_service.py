"""Central business-logic service for research lifecycle management."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

from deep_research.config import DepthConfig, DepthPreset, Settings, get_settings
from deep_research.db.engine import get_session
from deep_research.db.models import ResearchStatus
from deep_research.db.repository import ResearchRepository
from deep_research.schemas.events import (
    CompletionEvent,
    ErrorEvent,
    StageStartEvent,
)
from deep_research.schemas.research import ResearchCreate, ResearchDetail, ResearchSummary
from deep_research.services.cost_tracker import CostTrackerCallback
from deep_research.services.event_emitter import get_event_emitter
from deep_research.services.pipeline import run_pipeline
from deep_research.services.stage_tracker import StageCallback

logger = logging.getLogger(__name__)


class ResearchService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def start_research(
        self,
        request: ResearchCreate,
        on_stage: StageCallback | None = None,
    ) -> ResearchDetail:
        research_id = uuid.uuid4()
        depth = request.depth
        limits = DepthConfig.get(depth)

        artifacts_dir = str(
            (self.settings.researches_dir / str(research_id)).resolve()
        )
        Path(artifacts_dir).mkdir(parents=True, exist_ok=True)
        (Path(artifacts_dir) / "notes").mkdir(exist_ok=True)
        (Path(artifacts_dir) / "sources").mkdir(exist_ok=True)

        config_snapshot: dict[str, Any] = {
            "depth": depth.value,
            "model": self.settings.default_model,
            **limits,
        }

        async with get_session() as session:
            repo = ResearchRepository(session)
            research = await repo.create(
                query=request.query,
                depth=depth.value,
                artifacts_dir=artifacts_dir,
                config_snapshot=config_snapshot,
            )
            research_id = research.id
            await repo.update_status(research_id, ResearchStatus.PLANNING)
            await repo.add_event(research_id, "research_started", payload=config_snapshot)

        emitter = get_event_emitter()
        await emitter.emit(
            StageStartEvent(research_id=research_id, stage="planning", stage_index=0)
        )

        try:
            pipeline_result = run_pipeline(
                query=request.query,
                artifacts_dir=artifacts_dir,
                settings=self.settings,
                depth=depth,
                on_stage=on_stage,
            )

            async with get_session() as session:
                repo = ResearchRepository(session)
                await repo.update_status(research_id, ResearchStatus.COMPLETED)
                await repo.add_event(
                    research_id,
                    "research_completed",
                    payload={
                        "sources_count": len(pipeline_result.search_results),
                        "report_length": len(pipeline_result.report),
                    },
                )
                await repo.add_cost(
                    research_id=research_id,
                    agent_name="pipeline",
                    model=self.settings.default_model,
                    tokens_input=pipeline_result.tokens_input,
                    tokens_output=pipeline_result.tokens_output,
                    estimated_cost_usd=CostTrackerCallback.estimate_cost(
                        self.settings.default_model,
                        pipeline_result.tokens_input,
                        pipeline_result.tokens_output,
                    ),
                )

            await emitter.emit(
                CompletionEvent(
                    research_id=research_id,
                    report_path=f"{artifacts_dir}/report.md",
                    elapsed_seconds=0,
                )
            )

        except Exception as exc:
            async with get_session() as session:
                repo = ResearchRepository(session)
                await repo.update_status(
                    research_id, ResearchStatus.FAILED, error=str(exc)
                )
                await repo.add_event(
                    research_id, "error", payload={"error": str(exc)}
                )
            await emitter.emit(
                ErrorEvent(
                    research_id=research_id,
                    message=str(exc),
                    recoverable=False,
                )
            )
            raise
        finally:
            await emitter.close(research_id)

        return await self.get_detail(research_id)

    async def get_detail(self, research_id: uuid.UUID) -> ResearchDetail:
        async with get_session() as session:
            repo = ResearchRepository(session)
            research = await repo.get(research_id)
            if research is None:
                raise ValueError(f"Research {research_id} not found")
            cost_info = await repo.get_total_cost(research_id)

        return ResearchDetail(
            id=research.id,
            query=research.query,
            status=research.status.value,
            depth=research.depth,
            config_snapshot=research.config_snapshot,
            artifacts_dir=research.artifacts_dir,
            started_at=research.started_at,
            completed_at=research.completed_at,
            error=research.error,
            created_at=research.created_at,
            updated_at=research.updated_at,
            total_tokens_input=cost_info["total_tokens_input"],
            total_tokens_output=cost_info["total_tokens_output"],
            total_cost_usd=cost_info["total_cost_usd"],
        )

    async def list_researches(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ResearchSummary]:
        status_enum = ResearchStatus(status) if status else None
        async with get_session() as session:
            repo = ResearchRepository(session)
            researches = await repo.list_all(status=status_enum, limit=limit, offset=offset)

        results: list[ResearchSummary] = []
        for r in researches:
            results.append(
                ResearchSummary(
                    id=r.id,
                    query=r.query,
                    status=r.status.value,
                    depth=r.depth,
                    created_at=r.created_at,
                    completed_at=r.completed_at,
                )
            )
        return results

    async def resume_research(self, research_id: uuid.UUID) -> ResearchDetail:
        async with get_session() as session:
            repo = ResearchRepository(session)
            research = await repo.get(research_id)
            if research is None:
                raise ValueError(f"Research {research_id} not found")
            if research.status not in (ResearchStatus.FAILED, ResearchStatus.CANCELLED):
                raise ValueError(
                    f"Cannot resume research in status {research.status.value}"
                )

        request = ResearchCreate(
            query=research.query,
            depth=DepthPreset(research.depth),
        )
        return await self.start_research(request)
