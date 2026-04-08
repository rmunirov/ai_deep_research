"""Data-access layer for research metadata."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from deep_research.db.models import CostRecord, Research, ResearchEvent, ResearchStatus


class ResearchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # -- Research CRUD --

    async def create(
        self,
        query: str,
        depth: str,
        artifacts_dir: str,
        config_snapshot: dict[str, Any] | None = None,
    ) -> Research:
        research = Research(
            query=query,
            depth=depth,
            artifacts_dir=artifacts_dir,
            config_snapshot=config_snapshot,
            status=ResearchStatus.PENDING,
        )
        self._session.add(research)
        await self._session.flush()
        return research

    async def get(self, research_id: uuid.UUID) -> Research | None:
        return await self._session.get(Research, research_id)

    async def list_all(
        self,
        status: ResearchStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Research]:
        stmt = select(Research).order_by(Research.created_at.desc()).offset(offset).limit(limit)
        if status is not None:
            stmt = stmt.where(Research.status == status)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        research_id: uuid.UUID,
        status: ResearchStatus,
        *,
        error: str | None = None,
    ) -> None:
        research = await self.get(research_id)
        if research is None:
            return
        research.status = status
        if error is not None:
            research.error = error
        now = datetime.now(UTC)
        if status == ResearchStatus.PENDING:
            research.started_at = now
        if status in (ResearchStatus.COMPLETED, ResearchStatus.FAILED, ResearchStatus.CANCELLED):
            research.completed_at = now
        await self._session.flush()

    # -- Events --

    async def add_event(
        self,
        research_id: uuid.UUID,
        event_type: str,
        agent_name: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> ResearchEvent:
        event = ResearchEvent(
            research_id=research_id,
            event_type=event_type,
            agent_name=agent_name,
            payload=payload,
        )
        self._session.add(event)
        await self._session.flush()
        return event

    # -- Cost tracking --

    async def add_cost(
        self,
        research_id: uuid.UUID,
        agent_name: str,
        model: str,
        tokens_input: int,
        tokens_output: int,
        estimated_cost_usd: Decimal,
    ) -> CostRecord:
        record = CostRecord(
            research_id=research_id,
            agent_name=agent_name,
            model=model,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            estimated_cost_usd=estimated_cost_usd,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_total_cost(self, research_id: uuid.UUID) -> dict[str, Any]:
        stmt = select(CostRecord).where(CostRecord.research_id == research_id)
        result = await self._session.execute(stmt)
        records = list(result.scalars().all())
        return {
            "total_tokens_input": sum(r.tokens_input for r in records),
            "total_tokens_output": sum(r.tokens_output for r in records),
            "total_cost_usd": sum(r.estimated_cost_usd for r in records),
            "records": len(records),
        }
