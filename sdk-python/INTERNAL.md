# Internal Development Guide

This document contains information for developers working on the AgentRPC Python SDK.

## Development Setup

1. Install uv (if not already installed): https://docs.astral.sh/uv/

2. Create virtual environment and install dependencies:
   ```bash
   make install
   ```
3. Activate virtual environment:
   ```bash
   source .venv/bin/activate
   ```

## Development Commands

The project uses a Makefile to streamline common development tasks:

- `make install`: Creates a virtual environment and installs dependencies using uv
- `make test`: Runs the test suite using pytest
- `make lint`: Runs ruff linter to check code quality
- `make format`: Formats code using ruff
- `make clean`: Removes build artifacts and cache files

## Testing

The test suite uses pytest and can be run with:
```bash
make test
```

Environment variables for testing can be set in a `.env` file:
- `INFERABLE_TEST_API_SECRET`: API secret for testing
- `INFERABLE_TEST_API_ENDPOINT`: API endpoint for testing

## Code Style

This project uses ruff for both linting and formatting. The configuration is in `pyproject.toml`.

Style guidelines:
- Line length: 88 characters (Black compatible)
- Python 3.8+ compatibility
- Double quotes for strings
- Import sorting using isort rules

## Release Process

1. Update version in `pyproject.toml`
2. Build and publish to PyPI:
   ```bash
   make publish
   ```
2. Build and publish to PyPI:
   ```bash
   python -m build
   python -m twine upload dist/*
   ```

## Dependencies

Dependencies are managed using uv for improved performance and reliability. Core dependencies are specified in `pyproject.toml` under `dependencies`, while development dependencies are under `optional-dependencies.dev`.
