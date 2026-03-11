from __future__ import annotations

from dataclasses import dataclass

from pawagent.core.agent import AgentDependencies


@dataclass(slots=True)
class Orchestrator:
    dependencies: AgentDependencies
