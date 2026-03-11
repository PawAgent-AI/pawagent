from __future__ import annotations

from pathlib import Path

from pawagent.core.unified_analysis import UnifiedMediaAnalysisService
from pawagent.expression.store import ExpressionLocalizationStore, InMemoryExpressionLocalizationStore
from pawagent.memory.store import AnalysisStore
from pawagent.models.analysis import ExpressionLocalizationRecord, ExpressionResult
from pawagent.personality.profiler import PersonalityProfiler
from pawagent.providers.base import BaseProvider


EXPRESSION_VERSION = "expression_render_v1"


class PetExpressionAgent:
    def __init__(
        self,
        provider: BaseProvider,
        memory_store: AnalysisStore,
        profiler: PersonalityProfiler,
        localization_store: ExpressionLocalizationStore | None = None,
    ) -> None:
        del profiler
        self._provider = provider
        self._analysis_service = UnifiedMediaAnalysisService(provider=provider, memory_store=memory_store)
        self._localization_store = localization_store or InMemoryExpressionLocalizationStore()

    def express_image(
        self,
        image_path: Path,
        pet_id: str,
        pet_name: str,
        species: str,
        modality: str = "image",
        locale: str = "en",
        style: str = "default",
    ) -> ExpressionResult:
        return self.express_media(
            path=image_path,
            pet_id=pet_id,
            pet_name=pet_name,
            species=species,
            modality=modality,
            locale=locale,
            style=style,
        )

    def express_media(
        self,
        path: Path,
        pet_id: str,
        pet_name: str,
        species: str,
        modality: str = "image",
        locale: str = "en",
        style: str = "default",
    ) -> ExpressionResult:
        del pet_name
        record = self._analysis_service.analyze(path=path, pet_id=pet_id, species=species, modality=modality)
        normalized_locale = locale.strip() or "en"
        cached = self._localization_store.get_record(
            content_hash=record.content_hash,
            analysis_version=record.analysis_version,
            expression_version=EXPRESSION_VERSION,
            locale=normalized_locale,
            style=style,
        )
        if cached is not None:
            return cached.expression

        if normalized_locale.lower().startswith("en"):
            expression = record.analysis.expression.model_copy(
                update={"locale": normalized_locale, "source_language": "en", "style": style}
            )
        else:
            raw = self._provider.render_expression(record.analysis, locale=normalized_locale, style=style)
            expression = ExpressionResult.model_validate(raw)

        self._localization_store.save_record(
            ExpressionLocalizationRecord(
                content_hash=record.content_hash,
                analysis_version=record.analysis_version,
                expression_version=EXPRESSION_VERSION,
                locale=normalized_locale,
                style=style,
                expression=expression,
                provider=self._provider.__class__.__name__,
                model=getattr(self._provider, "_model", ""),
            )
        )
        return expression
