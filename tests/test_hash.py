"""
Tests for app/utilities/Hash.py

Verifies that Hash.hash() uses SHA-256 after the MD5 → SHA-256 fix in PR #30.
MD5 is cryptographically broken and was being used to generate security-sensitive
IDs stored in Redis and matched on call hangup.
"""
import hashlib
from app.utilities.Hash import Hash


def test_hash_returns_sha256():
    """Hash.hash() output must match hashlib.sha256 for the same input."""
    value = "test-string"
    assert Hash.hash(value) == hashlib.sha256(value.encode()).hexdigest()


def test_hash_length():
    """SHA-256 hex digest is always exactly 64 characters."""
    assert len(Hash.hash("anything")) == 64


def test_hash_is_deterministic():
    """Same input must always produce the same hash."""
    assert Hash.hash("abc") == Hash.hash("abc")


def test_hash_different_inputs_differ():
    """Different inputs must produce different hashes."""
    assert Hash.hash("foo") != Hash.hash("bar")


def test_hash_not_md5():
    """Explicitly confirm MD5 is not being used — MD5 digest is 32 chars, not 64."""
    value = "test"
    md5_result = hashlib.md5(value.encode()).hexdigest()
    assert Hash.hash(value) != md5_result
    assert len(md5_result) == 32   # MD5 is 32 hex chars
    assert len(Hash.hash(value)) == 64  # SHA-256 is 64 hex chars
