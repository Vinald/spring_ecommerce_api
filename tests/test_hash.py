"""Tests for app/utilities/Hash.py"""
import hashlib
import pytest
from app.utilities.Hash import Hash


def test_hash_returns_sha256():
    """Hash.hash() must use SHA-256, not MD5."""
    value = "test-string"
    result = Hash.hash(value)
    expected = hashlib.sha256(value.encode()).hexdigest()
    assert result == expected


def test_hash_length():
    """SHA-256 hex digest is always 64 characters."""
    assert len(Hash.hash("anything")) == 64


def test_hash_is_deterministic():
    """Same input always produces the same hash."""
    assert Hash.hash("abc") == Hash.hash("abc")


def test_hash_different_inputs():
    """Different inputs must produce different hashes."""
    assert Hash.hash("foo") != Hash.hash("bar")


def test_hash_not_md5():
    """Explicitly confirm MD5 is NOT being used."""
    value = "test"
    md5_result = hashlib.md5(value.encode()).hexdigest()
    assert Hash.hash(value) != md5_result
