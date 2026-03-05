"""Shared test fixtures and configuration."""

import os

import pytest
from dotenv import load_dotenv

# Load .env from project root or orchestrator root
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


@pytest.fixture
def qdrant_url() -> str:
    url = os.environ.get("QDRANT_URL", "")
    if not url:
        pytest.skip("QDRANT_URL not set")
    return url


@pytest.fixture
def qdrant_api_key() -> str:
    key = os.environ.get("QDRANT_API_KEY", "")
    if not key:
        pytest.skip("QDRANT_API_KEY not set")
    return key


@pytest.fixture
def supabase_url() -> str:
    url = os.environ.get("SUPABASE_URL", "")
    if not url:
        pytest.skip("SUPABASE_URL not set")
    return url


@pytest.fixture
def supabase_key() -> str:
    key = os.environ.get("SUPABASE_KEY", "")
    if not key:
        pytest.skip("SUPABASE_KEY not set")
    return key
