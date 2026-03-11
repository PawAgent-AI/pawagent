from __future__ import annotations


class ProviderError(RuntimeError):
    """Base error for provider failures."""


class ProviderAuthenticationError(ProviderError):
    """Raised when provider credentials are missing or invalid."""


class ProviderExecutionError(ProviderError):
    """Raised when the provider backend or CLI invocation fails."""


class ProviderOutputParseError(ProviderError):
    """Raised when provider output cannot be parsed into the expected schema."""
