"""Tests for marshmallow request validation schemas."""
import pytest
from app.schemas.schemas import (
    LoginSchema, UserCreateSchema, UserUpdateSchema,
    AppCreateSchema, ReportCreateSchema, ProfileUpdateSchema,
)
from app.utilities.validation import validate_request

# Test data constants - placeholder values for testing only
TEST_VALID_PASSWORD = 'TestPass123!'
TEST_WEAK_PASSWORD = 'weak'
TEST_PASSWORD_SHORT = 'x'



# ── Login ─────────────────────────────────────────────────────────────────────

def test_login_valid():
    errors, data = validate_request({'username': 'a@b.com', 'password': TEST_VALID_PASSWORD}, LoginSchema())
    assert errors is None
    assert data['username'] == 'a@b.com'


def test_login_missing_password():
    errors, data = validate_request({'username': 'a@b.com'}, LoginSchema())
    assert errors is not None
    assert data is None


def test_login_invalid_email():
    errors, data = validate_request({'username': 'not-an-email', 'password': TEST_PASSWORD_SHORT}, LoginSchema())
    assert errors is not None


# ── Users ─────────────────────────────────────────────────────────────────────

def test_user_create_valid():
    errors, data = validate_request(
        {'email': 'u@example.com', 'password': TEST_VALID_PASSWORD, 'role': 'user'},
        UserCreateSchema()
    )
    assert errors is None


def test_user_create_invalid_role():
    errors, data = validate_request(
        {'email': 'u@example.com', 'password': TEST_VALID_PASSWORD, 'role': 'superuser'},
        UserCreateSchema()
    )
    assert errors is not None


def test_user_create_missing_email():
    errors, data = validate_request({'password': TEST_VALID_PASSWORD, 'role': 'user'}, UserCreateSchema())
    assert errors is not None


# ── Applications ──────────────────────────────────────────────────────────────

def test_app_create_valid():
    errors, data = validate_request({
        'name': 'MyApp',
        'voice_url': 'http://example.com/voice',
        'status_url': 'http://example.com/status',
        'phone': '256700000000',
        'caller_id': '256700000001',
        'toll_free': '',
    }, AppCreateSchema())
    assert errors is None


def test_app_create_invalid_url():
    errors, data = validate_request({
        'name': 'MyApp',
        'voice_url': 'not-a-url',
        'status_url': 'http://example.com/status',
    }, AppCreateSchema())
    assert errors is not None


# ── Profile ───────────────────────────────────────────────────────────────────

def test_profile_valid_password():
    errors, data = validate_request(
        {'oldPassword': TEST_VALID_PASSWORD, 'password': TEST_VALID_PASSWORD},
        ProfileUpdateSchema()
    )
    assert errors is None


def test_profile_weak_password():
    errors, data = validate_request(
        {'oldPassword': TEST_VALID_PASSWORD, 'password': TEST_WEAK_PASSWORD},
        ProfileUpdateSchema()
    )
    assert errors is not None
