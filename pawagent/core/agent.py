from __future__ import annotations

from dataclasses import dataclass

from pawagent.memory.store import InMemoryAnalysisStore
from pawagent.personality.profiler import PersonalityProfiler
from pawagent.providers.base import BaseProvider


@dataclass(slots=True)
class AgentDependencies:
    provider: BaseProvider
    memory_store: InMemoryAnalysisStore
    profiler: PersonalityProfiler
