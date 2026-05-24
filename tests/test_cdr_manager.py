"""
Tests for app/manager/CDRManager.py

Focuses on the midnight boundary bug fixed in PR #30:
  Old code: subtracted two HH:MM:SS strings — negative duration for calls spanning midnight.
  Fix: store a Unix float timestamp (call_start_timestamp) alongside the formatted time
       and subtract timestamps instead of parsing strings.
"""
import json
import time
from unittest.mock import MagicMock


def _make_cdr_manager():
    """Build a CDRManager with fully mocked dependencies."""
    from app.manager.CDRManager import CDRManager
    cache = MagicMock()
    database = MagicMock()
    logger = MagicMock()
    return CDRManager(cache, database, logger), cache, database, logger


def test_update_call_start_time_stores_unix_timestamp():
    """
    update_call_start_time must store call_start_timestamp as a Unix float.
    This is the key field used by end_call_and_flush_cdr_to_db() to calculate
    duration correctly across midnight.
    """
    mgr, cache, db, _ = _make_cdr_manager()
    cache.get.return_value = json.dumps({'call_state': 'INITIATED'}).encode()

    mgr.update_call_start_time('call-123')

    saved = json.loads(cache.save.call_args[0][1])
    assert 'call_start_timestamp' in saved
    assert isinstance(saved['call_start_timestamp'], float)
    assert saved['call_state'] == 'ANSWERED'


def test_end_call_uses_unix_timestamp_for_duration():
    """
    Duration must be derived from Unix timestamps, not HH:MM:SS strings.
    A call started ~90 seconds ago should have duration ≈ 90.
    """
    mgr, cache, db, _ = _make_cdr_manager()
    start_ts = time.time() - 90
    cdr = _base_cdr(call_start_timestamp=start_ts, call_start_time='10:00:00')
    cache.get.return_value = json.dumps(cdr).encode()

    mgr.end_call_and_flush_cdr_to_db('call-123')

    inserted = db.insert.call_args[0][0]
    # Allow ±3 seconds for test execution time
    assert 87 <= inserted['duration'] <= 93


def test_midnight_boundary_never_negative():
    """
    A call started 5 minutes ago must have a non-negative duration even if
    the HH:MM:SS strings would produce a negative delta (e.g. 23:58 → 00:02).
    """
    mgr, cache, db, _ = _make_cdr_manager()
    cdr = _base_cdr(call_start_timestamp=time.time() - 300, call_start_time='23:58:00')
    cache.get.return_value = json.dumps(cdr).encode()

    mgr.end_call_and_flush_cdr_to_db('call-456')

    assert db.insert.call_args[0][0]['duration'] >= 0


def test_internal_timestamp_not_inserted_into_db():
    """
    call_start_timestamp is an internal field used only for duration math.
    It must be stripped before inserting into the CDR table (not a DB column).
    """
    mgr, cache, db, _ = _make_cdr_manager()
    cdr = _base_cdr(call_start_timestamp=time.time() - 60, call_start_time='10:00:00')
    cache.get.return_value = json.dumps(cdr).encode()

    mgr.end_call_and_flush_cdr_to_db('call-789')

    assert 'call_start_timestamp' not in db.insert.call_args[0][0]


def test_flush_cdr_to_db_sets_call_state():
    """flush_cdr_to_db must write the provided call_state value to the DB."""
    mgr, cache, db, _ = _make_cdr_manager()
    cache.get.return_value = json.dumps(_base_cdr()).encode()

    mgr.flush_cdr_to_db('call-999', 'FAILED')

    assert db.insert.call_args[0][0]['call_state'] == 'FAILED'


def test_flush_cdr_strips_internal_timestamp():
    """flush_cdr_to_db must also strip call_start_timestamp before DB insert."""
    mgr, cache, db, _ = _make_cdr_manager()
    cdr = _base_cdr(call_start_timestamp=time.time())
    cache.get.return_value = json.dumps(cdr).encode()

    mgr.flush_cdr_to_db('call-888', 'NO_ANSWER')

    assert 'call_start_timestamp' not in db.insert.call_args[0][0]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _base_cdr(**overrides):
    """Return a minimal valid CDR dict, with optional field overrides."""
    base = {
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
    base.update(overrides)
    return base
