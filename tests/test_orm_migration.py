"""
Tests for the dual DB layer consolidation (fix/remaining-improvements).

Verifies that Apps and CDRManager now use SQLAlchemy ORM sessions
instead of raw PyMySQL Database instances.
"""
from unittest.mock import MagicMock, patch, call
import json
import time


# ── Apps ORM migration ────────────────────────────────────────────────────────

def test_apps_uses_session_factory_not_database():
    """
    Apps.__init__ must accept a session_factory (callable returning a session),
    not a Database instance. Passing a mock callable must not raise.
    """
    from app.api.Apps import Apps
    session_factory = MagicMock()
    session_factory.return_value = MagicMock()
    logger = MagicMock()
    # Should not raise — no Database import or attribute access.
    apps = Apps(session_factory, logger)
    assert apps is not None


def test_apps_get_data_uses_orm_query():
    """
    get_data() must call session.query(App).filter(...).first()
    rather than cursor.execute(raw_sql).
    """
    from app.api.Apps import Apps
    from app.models.models import App

    mock_app = MagicMock(spec=App)
    mock_app.id = 1
    mock_app.name = 'TestApp'
    mock_app.token = 'tok-abc'
    mock_app.phone = '256700000000'
    mock_app.toll_free = ''
    mock_app.caller_id = '256700000001'
    mock_app.voice_url = 'http://example.com/voice'
    mock_app.status_url = 'http://example.com/status'
    mock_app.user_id = 1

    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = mock_app

    session_factory = MagicMock(return_value=mock_session)
    apps = Apps(session_factory, MagicMock())

    result = apps.get_data('tok-abc')

    assert result['name'] == 'TestApp'
    assert result['token'] == 'tok-abc'
    # Verify ORM query was used — not cursor.execute
    mock_session.query.assert_called_once()
    mock_session.close.assert_called_once()


def test_apps_get_data_returns_empty_dict_when_not_found():
    """get_data must return {} when the token does not match any app."""
    from app.api.Apps import Apps

    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = None
    session_factory = MagicMock(return_value=mock_session)

    apps = Apps(session_factory, MagicMock())
    result = apps.get_data('nonexistent-token')
    assert result == {}


# ── CDRManager ORM migration ──────────────────────────────────────────────────

def test_cdr_manager_uses_session_factory_not_database():
    """
    CDRManager.__init__ must accept a session_factory, not a Database instance.
    """
    from app.manager.CDRManager import CDRManager
    session_factory = MagicMock(return_value=MagicMock())
    mgr = CDRManager(MagicMock(), session_factory, MagicMock())
    assert mgr is not None


def test_cdr_insert_uses_orm_add_not_raw_insert():
    """
    _insert_cdr() must call session.add(cdr_instance) and session.commit(),
    not Database.insert(dict, table_name).
    """
    from app.manager.CDRManager import CDRManager

    mock_session = MagicMock()
    session_factory = MagicMock(return_value=mock_session)
    mgr = CDRManager(MagicMock(), session_factory, MagicMock())

    mgr._insert_cdr({
        'app_name': 'TestApp', 'caller_id': '256700000000',
        'dialed_number': '256711111111', 'call_direction': 'OUTGOING',
        'call_state': 'ANSWERED', 'peer': 'airtel',
        'call_id': 'cid-1', 'external_id': 'eid-1', 'token': 'tok-1',
    })

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.close.assert_called_once()


def test_get_number_of_processed_calls_uses_orm():
    """get_number_of_processed_calls must use ORM count(), not raw SQL."""
    from app.manager.CDRManager import CDRManager

    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.count.return_value = 42
    session_factory = MagicMock(return_value=mock_session)

    mgr = CDRManager(MagicMock(), session_factory, MagicMock())
    count = mgr.get_number_of_processed_calls()

    assert count == 42
    mock_session.query.assert_called_once()
