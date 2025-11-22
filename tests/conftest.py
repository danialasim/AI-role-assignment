"""Pytest configuration for test suite."""

import pytest


def pytest_addoption(parser):
    """Add custom command-line options for pytest."""
    parser.addoption(
        "--run-real-api",
        action="store_true",
        default=False,
        help="Run tests that make real API calls (consumes API credits)"
    )


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "real_api: mark test as requiring real API calls (use --run-real-api to run)"
    )
