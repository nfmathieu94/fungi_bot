#!/usr/bin/python3

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import getpass
import json


@dataclass
class AnalysisRecord:
    """
    Structured summary of a completed analysis/workflow run.

    This is meant to be serialized as JSON and embedded in:
      - tool outputs (for the agent to see)
      - LLM responses (so ADK memory consolidation can store it)
    """
    type: str
    app_name: str
    user_id: str
    workflow_name: str
    created_at: str  # ISO 8601
    params: Dict[str, Any]
    summary_text: str
    result_stats: Dict[str, Any]
    figure_paths: List[str]
    tags: List[str]

    @classmethod
    def create(
        cls,
        workflow_name: str,
        params: Dict[str, Any],
        summary_text: str,
        result_stats: Optional[Dict[str, Any]] = None,
        figure_paths: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        app_name: str = "fungi_bot",
        user_id: Optional[str] = None,
    ) -> "AnalysisRecord":
        if user_id is None:
            # For now, default to HPC username. Later we can pass an explicit user_id.
            user_id = getpass.getuser()

        if result_stats is None:
            result_stats = {}

        if figure_paths is None:
            figure_paths = []

        if tags is None:
            tags = []

        created_at = datetime.now(timezone.utc).isoformat()

        return cls(
            type="fungibot_analysis",
            app_name=app_name,
            user_id=user_id,
            workflow_name=workflow_name,
            created_at=created_at,
            params=params,
            summary_text=summary_text,
            result_stats=result_stats,
            figure_paths=figure_paths,
            tags=tags,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, *, indent: Optional[int] = None) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

