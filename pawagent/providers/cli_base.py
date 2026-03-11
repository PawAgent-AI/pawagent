from __future__ import annotations

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable

from pawagent.models.media import ImageInput
from pawagent.providers.base import BaseProvider
from pawagent.providers.errors import ProviderExecutionError
from pawagent.providers.parsing import normalize_unified_payload, parse_json_text


class CliAgentProvider(BaseProvider, ABC):
    def __init__(
        self,
        runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    ) -> None:
        self._runner = runner or subprocess.run

    def analyze_image(self, image: ImageInput, prompt: str) -> dict[str, object]:
        result = self._runner(
            self.build_command(image=image, prompt=prompt),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or self.default_error_message()
            raise ProviderExecutionError(f"{self.provider_label()} failed: {message}")

        output_text = self.read_output(result=result)
        return self.parse_payload(output_text)

    @abstractmethod
    def build_command(self, image: ImageInput, prompt: str) -> list[str]:
        raise NotImplementedError

    def read_output(self, result: subprocess.CompletedProcess[str]) -> str:
        return result.stdout

    @abstractmethod
    def provider_label(self) -> str:
        raise NotImplementedError

    def default_error_message(self) -> str:
        return "Unknown CLI execution error."

    def parse_payload(self, output_text: str) -> dict[str, object]:
        return normalize_unified_payload(parse_json_text(output_text))

    def resolve_image_path(self, image: ImageInput) -> Path:
        return image.path.resolve()
