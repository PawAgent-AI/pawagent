# Contributing to PawAgent

Thank you for your interest in contributing to PawAgent! This guide will help you get started.

## Getting Started

### Prerequisites

- Python 3.11 or later
- Git

### Setup

1. Fork and clone the repository:

```bash
git clone https://github.com/PawAgent-AI/pawagent.git
cd pawagent
```

2. Install the package in development mode:

```bash
pip install -e .
```

3. Install test dependencies:

```bash
pip install pytest
```

4. (Optional) Install identity extras for working on the identity module:

```bash
pip install -e ".[identity]"
```

### Running Tests

```bash
pytest
```

All tests should pass before submitting a pull request. The test suite uses the built-in `MockProvider` so no API keys are needed.

## Project Structure

```text
pawagent/
├── cli/              # CLI entry point
├── docs/             # Architecture and concept documentation
├── examples/         # Usage examples
├── pawagent/
│   ├── agents/       # Task-specific agents (emotion, behavior, etc.)
│   ├── core/         # Core abstractions and unified analysis service
│   ├── expression/   # Expression localization and caching
│   ├── identity/     # Pet identity enrollment and verification
│   ├── memory/       # Analysis record storage and caching
│   ├── models/       # Pydantic data models
│   ├── personality/  # Personality profiling from analysis history
│   ├── providers/    # Model provider integrations
│   ├── video/        # Video analysis pipeline
│   └── vision/       # Image analysis pipeline
└── tests/            # Test suite
```

See [docs/architecture.md](docs/architecture.md) for a detailed architecture diagram and data flow description.

## Contribution Areas

### Vision and Video Analysis

- Improve prompt quality for more accurate emotion, behavior, and motivation detection
- Add support for new image/video formats
- Optimize preprocessing pipelines

### Provider Integrations

- Add new model provider implementations (implement `BaseProvider`)
- Improve existing provider error handling and response parsing
- Add provider-specific optimizations

### Identity Verification

- Improve cropping accuracy for different pet poses
- Experiment with alternative embedding models
- Add multi-pet detection support within a single image

### Behavior and Motivation Quality

- Refine behavior classification labels
- Improve motivation inference from emotion and behavior signals
- Add species-specific behavior frameworks

### Documentation and Benchmarks

- Improve API documentation
- Add usage examples for common workflows
- Create quality benchmarks for analysis accuracy

## How to Contribute

### Reporting Issues

- Use [GitHub Issues](https://github.com/PawAgent-AI/pawagent/issues) to report bugs or suggest features
- Include reproduction steps, expected behavior, and actual behavior
- Mention your Python version and OS

### Submitting Pull Requests

1. Create a feature branch from `main`:

```bash
git checkout -b feature/your-feature-name
```

2. Make your changes, following the code style guidelines below.

3. Add or update tests for your changes.

4. Run the full test suite:

```bash
pytest
```

5. Commit with a clear message:

```bash
git commit -m "Add support for XYZ"
```

6. Push and open a pull request against `main`.

## Code Style Guidelines

### General Principles

- **Keep it simple.** Avoid over-engineering. Add only what is needed for the current task.
- **Use type hints.** All function signatures should include type annotations.
- **Use Pydantic models** for structured data. Define new models in `pawagent/models/`.
- **Follow existing patterns.** Look at similar modules for structure and naming conventions.

### Logging

PawAgent uses Python's standard `logging` module. When adding logging to a module:

```python
import logging

logger = logging.getLogger(__name__)
```

Use appropriate log levels:
- `DEBUG`: Detailed diagnostic information (e.g., cache lookups, internal state)
- `INFO`: Key operations and milestones (e.g., analysis started, enrollment complete)
- `WARNING`: Unexpected but recoverable situations
- `ERROR`: Failures that prevent an operation from completing

### Providers

When adding a new provider:

1. Create a new file in `pawagent/providers/`.
2. Subclass `BaseProvider` and implement `analyze_image`.
3. Optionally implement `analyze_video`, `analyze_audio`, and `render_expression`.
4. Register the provider in `pawagent/providers/factory.py`.
5. Add the provider choice to `cli/main.py`.
6. Write tests using mock/fake API clients (see `tests/test_openai_provider.py` for reference).

### Tests

- Place tests in the `tests/` directory with the naming pattern `test_<module>.py`.
- Use `MockProvider` for tests that need a provider.
- Use `tmp_path` (pytest fixture) for any file I/O in tests.
- Tests should be self-contained and not require API keys or network access.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
