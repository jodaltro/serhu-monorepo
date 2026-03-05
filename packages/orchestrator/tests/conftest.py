"""Shared test fixtures and configuration."""

import os
import socket

import pytest
from dotenv import load_dotenv

# Load .env from project root or orchestrator root
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


def _can_resolve(url: str) -> bool:
    """Check if a URL's hostname can be resolved (basic connectivity check)."""
    try:
        from urllib.parse import urlparse

        hostname = urlparse(url).hostname
        if hostname:
            socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_STREAM)
        return True
    except (socket.gaierror, OSError):
        return False


@pytest.fixture
def qdrant_url() -> str:
    url = os.environ.get("QDRANT_URL", "")
    if not url:
        pytest.skip("QDRANT_URL not set")
    if not _can_resolve(url):
        pytest.skip(f"Cannot resolve Qdrant host (network unavailable): {url}")
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
    if not _can_resolve(url):
        pytest.skip(f"Cannot resolve Supabase host (network unavailable): {url}")
    return url


@pytest.fixture
def supabase_key() -> str:
    key = os.environ.get("SUPABASE_KEY", "")
    if not key:
        pytest.skip("SUPABASE_KEY not set")
    return key
