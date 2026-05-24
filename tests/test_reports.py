"""
Tests for Reports._build_cron_expression and ReportTypes._validate_report_sql.

_build_cron_expression: was duplicated verbatim in __post and __put (PR #33 fix).
_validate_report_sql:   enforces SELECT-only constraint on stored report SQL (PR #30 fix).
"""
import pytest
from app.api.Reports import Reports
from app.api.ReportTypes import _validate_report_sql


# ── Cron expression builder ───────────────────────────────────────────────────

def test_cron_not_scheduled_returns_none():
    """scheduled=0 must always return None regardless of other params."""
    assert Reports._build_cron_expression(0, 'daily', '09:00', '1') is None


def test_cron_daily():
    """Daily schedule at 09:30 → '30 09 * * *'"""
    assert Reports._build_cron_expression(1, 'daily', '09:30', '1') == '30 09 * * *'


def test_cron_weekly():
    """Weekly on Tuesday at 08:00 → '00 08 * * 2'"""
    assert Reports._build_cron_expression(1, 'weekly', '08:00', '2') == '00 08 * * 2'


def test_cron_monthly():
    """Monthly always uses first of month at midnight regardless of time param."""
    assert Reports._build_cron_expression(1, 'monthly', '12:00', '1') == '0 0 1 * *'


# ── SQL SELECT-only allowlist ─────────────────────────────────────────────────

def test_valid_select_passes():
    """A plain SELECT must be accepted."""
    ok, msg = _validate_report_sql("SELECT * FROM cdr")
    assert ok is True and msg is None


def test_valid_select_with_conditions():
    """SELECT with WHERE and string literals must be accepted."""
    ok, _ = _validate_report_sql("SELECT id, phone FROM cdr WHERE call_state = 'ANSWERED'")
    assert ok is True


def test_rejects_non_select():
    """Any statement that does not start with SELECT must be rejected."""
    ok, msg = _validate_report_sql("DROP TABLE cdr")
    assert ok is False
    assert 'SELECT' in msg


def test_rejects_delete_keyword():
    """DELETE embedded in a SELECT must be rejected."""
    ok, msg = _validate_report_sql("SELECT id FROM cdr; DELETE FROM cdr")
    assert ok is False and 'delete' in msg.lower()


def test_rejects_insert():
    ok, _ = _validate_report_sql("INSERT INTO cdr VALUES (1)")
    assert ok is False


def test_rejects_update():
    ok, _ = _validate_report_sql("UPDATE cdr SET call_state='X'")
    assert ok is False


def test_rejects_sql_line_comment():
    """-- comment injection must be blocked."""
    ok, _ = _validate_report_sql("SELECT * FROM cdr -- drop table cdr")
    assert ok is False


def test_rejects_block_comment():
    """/* */ comment injection must be blocked."""
    ok, _ = _validate_report_sql("SELECT * FROM cdr /* injected */")
    assert ok is False


def test_validation_is_case_insensitive():
    """Forbidden keywords in mixed case must still be caught."""
    ok, _ = _validate_report_sql("SELECT * FROM cdr; DrOp TaBlE cdr")
    assert ok is False
