"""Tests for app/manager/CDRManager.py"""
import json
import time
import pytest
from unittest.mock import MagicMock, patch, call


def _make_cdr_manager():
    """Build a CDRManager with mocked dependencies."""
    from app.manager.CDRManager import CDRManager
    cache = MagicMock()
    database = MagicMock()
    logger = MagicMock()
    return CDRManager(cache, database, logger), cache, database, logger


def test_update_call_start_time_stores_unix_timestamp():
    """update_call_start_time must store call_start_timestamp (Unix float)."""
    mgr, cache, db, _ = _make_cdr_manager()
    existing = {'call_state': 'INITIATED', 'call_start_time': None}
    cache.get.return_value = json.dumps(existing).encode()

    mgr.update_call_start_time('call-123')

    saved = json.loads(cache.save.call_args[0][1])
    assert 'call_start_timestamp' in saved
    assert isinstance(saved['call_start_timestamp'], float)
    assert saved['call_state'] == 'ANSWERED'


def test_end_call_uses_unix_timestamp_for_duration():
    """Duration must be calculated from Unix timestamps, not HH:MM:SS strings."""
    mgr, cache, db, _ = _make_cdr_manager()
    start_ts = time.time() - 90  # 90 seconds ago
    cdr = {
        'call_start_time': '23:00:00',
        'call_start_timestamp': start_ts,
        'caller_id': '256700000000',
        'dialed_number': '256711111111',
        'call_direction': 'OUTGOING',
        'app_name': 'TestApp',
        'creation_date': '2024-01-01 00:00:00',
        'peer': 'airtel',
        'call_id': 'cid-1',
        'external_id': 'eid-1',
        'token': 'tok-1',
    }
    cache.get.return_value = json.dumps(cdr).encode()

    mgr.end_call_and_flush_cdr_to_db('call-123')

    inserted = db.insert.call_args[0][0]
    # Duration should be ~90 seconds (allow ±3s for test execution time)
    assert 87 <= inserted['duration'] <= 93


def test_end_call_midnight_boundary():
    """Duration must never be negative even for calls spanning midnight."""
    mgr, cache, db, _ = _make_cdr_manager()
    # Simulate a call that started 5 minutes ago (crosses midnight in the old code)
    start_ts = time.time() - 300
    cdr = {
        'call_start_time': '23:58:00',
        'call_start_timestamp': start_ts,
        'caller_id': '256700000000',
        'dialed_number': '256711111111',
        'call_direction': 'OUTGOING',
        'app_name': 'TestApp',
        'creation_date': '2024-01-01 00:00:00',
        'peer': 'airtel',
        'call_id': 'cid-2',
        'external_id': 'eid-2',
        'token': 'tok-2',
    }
    cache.get.return_value = json.dumps(cdr).encode()

    mgr.end_call_and_flush_cdr_to_db('call-456')

    inserted = db.insert.call_args[0][0]
    assert inserted['duration'] >= 0


def test_flush_cdr_removes_internal_timestamp():
    """The call_start_timestamp field must not be inserted into the DB."""
    mgr, cache, db, _ = _make_cdr_manager()
    cdr = {
        'call_start_time': '10:00:00',
        'call_start_timestamp': time.time() - 60,
        'caller_id': '256700000000',
        'dialed_number': '256711111111',
        'call_direction': 'OUTGOING',
        'app_name': 'TestApp',
        'creation_date': '2024-01-01 00:00:00',
        'peer': 'airtel',
        'call_id': 'cid-3',
        'external_id': 'eid-3',
        'token': 'tok-3',
    }
    cache.get.return_value = json.dumps(cdr).encode()
    mgr.end_call_and_flush_cdr_to_db('call-789')

    inserted = db.insert.call_args[0][0]
    assert 'call_start_timestamp' not in inserted


def test_flush_cdr_to_db_sets_call_state():
    """flush_cdr_to_db must write the provided call_state to the DB."""
    mgr, cache, db, _ = _make_cdr_manager()
    cdr = {
        'caller_id': '256700000000', 'dialed_number': '256711111111',
        'call_direction': 'OUTGOING', 'app_name': 'TestApp',
        'creation_date': '2024-01-01 00:00:00', 'peer': 'airtel',
        'call_id': 'cid-4', 'external_id': 'eid-4', 'token': 'tok-4',
    }
    cache.get.return_value = json.dumps(cdr).encode()
    mgr.flush_cdr_to_db('call-999', 'FAILED')

    inserted = db.insert.call_args[0][0]
    assert inserted['call_state'] == 'FAILED'
