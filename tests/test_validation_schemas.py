"""
Tests for marshmallow request validation schemas (app/schemas/schemas.py)
and the validate_request() helper (app/utilities/validation.py).

These schemas were added in PR #33 to replace bare request.form[key] access
which raised KeyError (HTTP 500) when a field was missing.

NOTE: Test passwords are generic placeholder values used only in tests and are not
actual credentials. Never use real passwords in test files.
"""
import os
from app.schemas.schemas import (
    LoginSchema, UserCreateSchema, UserUpdateSchema,
    AppCreateSchema, ReportCreateSchema, ProfileUpdateSchema,
)
from app.utilities.validation import validate_request

# Test data constants - placeholder values for testing only
TEST_VALID_PASSWORD = os.environ.get('TEST_PASSWORD', 'TestPass123!')
TEST_WEAK_PASSWORD = 'weak'
TEST_PASSWORD_SHORT = 'x'


# ── Login ─────────────────────────────────────────────────────────────────────

def test_login_valid():
    errors, data = validate_request({'username': 'a@b.com', 'password': TEST_VALID_PASSWORD}, LoginSchema())
    assert errors is None and data['username'] == 'a@b.com'


def test_login_missing_password_returns_error():
    """Missing required field must return an error string, not raise KeyError."""
    errors, data = validate_request({'username': 'a@b.com'}, LoginSchema())
    assert errors is not None and data is None


def test_login_invalid_email_format():
    """username must be a valid email address."""
    errors, _ = validate_request({'username': 'not-an-email', 'password': TEST_PASSWORD_SHORT}, LoginSchema())
    assert errors is not None


# ── Users ─────────────────────────────────────────────────────────────────────

def test_user_create_valid():
    errors, _ = validate_request(
        {'email': 'u@example.com', 'password': TEST_VALID_PASSWORD, 'role': 'user'},
        UserCreateSchema()
    )
    assert errors is None


def test_user_create_invalid_role_rejected():
    """role must be one of: admin, user — anything else is rejected."""
    errors, _ = validate_request(
        {'email': 'u@example.com', 'password': TEST_VALID_PASSWORD, 'role': 'superuser'},
        UserCreateSchema()
    )
    assert errors is not None


def test_user_create_missing_email_rejected():
    errors, _ = validate_request({'password': TEST_VALID_PASSWORD, 'role': 'user'}, UserCreateSchema())
    assert errors is not None


# ── Applications ──────────────────────────────────────────────────────────────

def test_app_create_valid():
    errors, _ = validate_request({
        'name': 'MyApp',
        'voice_url': 'http://example.com/voice',
        'status_url': 'http://example.com/status',
        'phone': '256700000000',
        'caller_id': '256700000001',
        'toll_free': '',
    }, AppCreateSchema())
    assert errors is None


def test_app_create_invalid_voice_url_rejected():
    """voice_url must be a valid URL — garbage saved silently would break call flows."""
    errors, _ = validate_request({
        'name': 'MyApp',
        'voice_url': 'not-a-url',
        'status_url': 'http://example.com/status',
    }, AppCreateSchema())
    assert errors is not None


# ── Profile password change ───────────────────────────────────────────────────

def test_profile_valid_password():
    errors, _ = validate_request(
        {'oldPassword': TEST_VALID_PASSWORD, 'password': TEST_VALID_PASSWORD},
        ProfileUpdateSchema()
    )
    assert errors is None


def test_profile_weak_password_rejected():
    """Password complexity rule: min 8 chars, must include upper, lower, digit."""
    errors, _ = validate_request(
        {'oldPassword': TEST_VALID_PASSWORD, 'password': TEST_WEAK_PASSWORD},
        ProfileUpdateSchema()
    )
    assert errors is not None
