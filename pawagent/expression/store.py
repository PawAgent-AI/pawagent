from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from pawagent.models.analysis import ExpressionLocalizationRecord


class ExpressionLocalizationStore(Protocol):
    def save_record(self, record: ExpressionLocalizationRecord) -> None: ...

    def get_record(
        self,
        content_hash: str,
        analysis_version: str,
        expression_version: str,
        locale: str,
        style: str = "default",
    ) -> ExpressionLocalizationRecord | None: ...


class InMemoryExpressionLocalizationStore:
    def __init__(self) -> None:
        self._records: dict[tuple[str, str, str, str, str], ExpressionLocalizationRecord] = {}

    def save_record(self, record: ExpressionLocalizationRecord) -> None:
        key = (
            record.content_hash,
            record.analysis_version,
            record.expression_version,
            record.locale,
            record.style,
        )
        self._records[key] = record

    def get_record(
        self,
        content_hash: str,
        analysis_version: str,
        expression_version: str,
        locale: str,
        style: str = "default",
    ) -> ExpressionLocalizationRecord | None:
        return self._records.get((content_hash, analysis_version, expression_version, locale, style))


class JsonExpressionLocalizationStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write_records([])

    def save_record(self, record: ExpressionLocalizationRecord) -> None:
        records = self._read_records()
        for index, existing in enumerate(records):
            if (
                existing.content_hash == record.content_hash
                and existing.analysis_version == record.analysis_version
                and existing.expression_version == record.expression_version
                and existing.locale == record.locale
                and existing.style == record.style
            ):
                records[index] = record
                break
        else:
            records.append(record)
        self._write_records(records)

    def get_record(
        self,
        content_hash: str,
        analysis_version: str,
        expression_version: str,
        locale: str,
        style: str = "default",
    ) -> ExpressionLocalizationRecord | None:
        for record in self._read_records():
            if (
                record.content_hash == content_hash
                and record.analysis_version == analysis_version
                and record.expression_version == expression_version
                and record.locale == locale
                and record.style == style
            ):
                return record
        return None

    def _read_records(self) -> list[ExpressionLocalizationRecord]:
        if not self._path.exists():
            return []
        payload = json.loads(self._path.read_text(encoding="utf-8"))
        return [ExpressionLocalizationRecord.model_validate(item) for item in payload]

    def _write_records(self, records: list[ExpressionLocalizationRecord]) -> None:
        payload = [record.model_dump(mode="json") for record in records]
        self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
