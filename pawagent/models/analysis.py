from __future__ import annotations

from pydantic import BaseModel, Field

from pawagent.models.behavior import BehaviorResult
from pawagent.models.mood import MoodResult
from pawagent.models.personality import PersonalityProfile
from pawagent.models.pet import Pet


class MotivationResult(BaseModel):
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    alternatives: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    uncertainty_note: str = ""


class ExpressionResult(BaseModel):
    plain_text: str
    pet_voice: str
    tone: str = ""
    grounded_in: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    locale: str = "en"
    source_language: str = "en"
    style: str = "default"

    @property
    def text(self) -> str:
        return self.pet_voice


class SpeciesAssessment(BaseModel):
    requested_species: str = ""
    observed_species: str
    confidence: float = Field(ge=0.0, le=1.0)
    used_framework: str = "other"
    mismatch_warning: str = ""


class UnifiedAnalysisResult(BaseModel):
    species: SpeciesAssessment = Field(
        default_factory=lambda: SpeciesAssessment(
            observed_species="other",
            confidence=0.0,
            used_framework="other",
        )
    )
    emotion: MoodResult
    behavior: BehaviorResult
    motivation: MotivationResult
    expression: ExpressionResult
    evidence: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    pet: Pet
    analysis: UnifiedAnalysisResult
    personality: PersonalityProfile
    summary: str

    @property
    def mood(self) -> MoodResult:
        return self.analysis.emotion

    @property
    def behavior(self) -> BehaviorResult:
        return self.analysis.behavior

    @property
    def motivation(self) -> MotivationResult:
        return self.analysis.motivation

    @property
    def expression(self) -> ExpressionResult:
        return self.analysis.expression


class AnalysisRecord(BaseModel):
    pet_id: str
    content_hash: str
    source_path: str
    source_modality: str = "image"
    analysis: UnifiedAnalysisResult
    provider: str = ""
    model: str = ""
    analysis_version: str = "unified_image_v1"
    prompt_version: str = "unified_image_v1"
    summary: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)

    @property
    def mood(self) -> MoodResult:
        return self.analysis.emotion


class ExpressionLocalizationRecord(BaseModel):
    content_hash: str
    analysis_version: str
    expression_version: str
    locale: str
    style: str = "default"
    expression: ExpressionResult
    provider: str = ""
    model: str = ""
