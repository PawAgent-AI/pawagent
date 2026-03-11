from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from pawagent.models.analysis import AnalysisRecord


class AnalysisStore(Protocol):
    def add_record(self, record: AnalysisRecord) -> None: ...

    def get_recent_analysis(self, pet_id: str, limit: int = 5) -> list[AnalysisRecord]: ...

    def count_records(self, pet_id: str) -> int: ...

    def get_cached_analysis(self, content_hash: str, analysis_version: str) -> AnalysisRecord | None: ...


class InMemoryAnalysisStore:
    def __init__(self) -> None:
        self._records: dict[str, list[AnalysisRecord]] = {}
        self._cache: dict[tuple[str, str], AnalysisRecord] = {}

    def add_record(self, record: AnalysisRecord) -> None:
        records = self._records.setdefault(record.pet_id, [])
        for index, existing in enumerate(records):
            if existing.content_hash == record.content_hash and existing.analysis_version == record.analysis_version:
                records[index] = record
                break
        else:
            records.append(record)
        self._cache[(record.content_hash, record.analysis_version)] = record

    def get_recent_analysis(self, pet_id: str, limit: int = 5) -> list[AnalysisRecord]:
        return list(self._records.get(pet_id, [])[-limit:])

    def count_records(self, pet_id: str) -> int:
        return len(self._records.get(pet_id, []))

    def get_cached_analysis(self, content_hash: str, analysis_version: str) -> AnalysisRecord | None:
        return self._cache.get((content_hash, analysis_version))


class JsonAnalysisStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write_records([])

    def add_record(self, record: AnalysisRecord) -> None:
        records = self._read_records()
        for index, existing in enumerate(records):
            if existing.pet_id == record.pet_id and existing.content_hash == record.content_hash and existing.analysis_version == record.analysis_version:
                records[index] = record
                break
        else:
            records.append(record)
        self._write_records(records)

    def get_recent_analysis(self, pet_id: str, limit: int = 5) -> list[AnalysisRecord]:
        records = [record for record in self._read_records() if record.pet_id == pet_id]
        return records[-limit:]

    def count_records(self, pet_id: str) -> int:
        return sum(1 for record in self._read_records() if record.pet_id == pet_id)

    def get_cached_analysis(self, content_hash: str, analysis_version: str) -> AnalysisRecord | None:
        for record in self._read_records():
            if record.content_hash == content_hash and record.analysis_version == analysis_version:
                return record
        return None

    def _read_records(self) -> list[AnalysisRecord]:
        if not self._path.exists():
            return []
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        return [AnalysisRecord.model_validate(item) for item in raw]

    def _write_records(self, records: list[AnalysisRecord]) -> None:
        payload = [record.model_dump(mode="json") for record in records]
        self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
