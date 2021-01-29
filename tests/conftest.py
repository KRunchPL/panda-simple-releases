from collections.abc import Generator

import pytest
from loguru import logger


@pytest.fixture(autouse=True)
def clean_loguru_handlers() -> Generator[None]:
    """
    Fixture to clean up loguru handlers before and after each test.

    This ensures that loguru does not retain any handlers from previous tests,
    which could lead to unexpected behavior or duplicate log entries.
    """
    logger.remove()  # Remove any existing handlers before the test
    yield
    logger.remove()  # Remove any existing handlers after the test
