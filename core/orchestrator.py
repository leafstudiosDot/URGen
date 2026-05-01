from __future__ import annotations

from core.config import PipelineConfig
from core.pipeline import PipelineResult, run_pipeline


class Orchestrator:
	def __init__(self, config: PipelineConfig) -> None:
		self._config = config

	def run(self, topic: str) -> PipelineResult:
		return run_pipeline(topic, self._config)
