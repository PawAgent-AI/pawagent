from __future__ import annotations

from pathlib import Path

from pawagent.breed_identifier import BreedIdentifier
from pawagent.providers.mock_provider import MockProvider


def test_identifies_golden_retriever() -> None:
    identifier = BreedIdentifier(provider=MockProvider())
    result = identifier.identify(Path("golden-retriever.jpg"))

    assert result.species == "dog"
    assert result.breed == "Golden Retriever"
    assert result.confidence >= 0.9
    assert any(a.breed == "Labrador Retriever" for a in result.alternatives)
    assert len(result.traits) > 0


def test_identifies_cat() -> None:
    identifier = BreedIdentifier(provider=MockProvider())
    result = identifier.identify(Path("cat.jpg"))

    assert result.species == "cat"
    assert result.breed is not None
    assert 0.0 <= result.confidence <= 1.0


def test_identifies_wild_animal_without_breed() -> None:
    identifier = BreedIdentifier(provider=MockProvider())
    result = identifier.identify(Path("fox.jpg"))

    assert result.species == "red fox"
    assert result.breed is None
    assert result.confidence > 0.0


def test_result_confidence_always_in_range() -> None:
    identifier = BreedIdentifier(provider=MockProvider())
    for filename in ("golden-retriever.jpg", "cat.jpg", "fox.jpg", "unknown.jpg"):
        result = identifier.identify(Path(filename))
        assert 0.0 <= result.confidence <= 1.0
        for alt in result.alternatives:
            assert 0.0 <= alt.confidence <= 1.0


def test_default_returns_dog() -> None:
    identifier = BreedIdentifier(provider=MockProvider())
    result = identifier.identify(Path("unknown-animal.jpg"))

    assert result.species == "dog"
    assert result.breed is not None
