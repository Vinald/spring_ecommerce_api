"""Tests for Reports._build_cron_expression and ReportTypes SQL validation."""
import pytest
from app.api.Reports import Reports
from app.api.ReportTypes import _validate_report_sql


# ── Cron expression builder ───────────────────────────────────────────────────

def test_cron_not_scheduled():
    assert Reports._build_cron_expression(0, 'daily', '09:00', '1') is None


def test_cron_daily():
    expr = Reports._build_cron_expression(1, 'daily', '09:30', '1')
    assert expr == '30 09 * * *'


def test_cron_weekly():
    expr = Reports._build_cron_expression(1, 'weekly', '08:00', '2')
    assert expr == '00 08 * * 2'


def test_cron_monthly():
    expr = Reports._build_cron_expression(1, 'monthly', '12:00', '1')
    assert expr == '0 0 1 * *'


# ── SQL allowlist validation ──────────────────────────────────────────────────

def test_valid_select():
    ok, msg = _validate_report_sql("SELECT * FROM cdr")
    assert ok is True
    assert msg is None


def test_valid_select_with_where():
    ok, _ = _validate_report_sql("SELECT id, phone FROM cdr WHERE call_state = 'ANSWERED'")
    assert ok is True


def test_rejects_drop():
    ok, msg = _validate_report_sql("DROP TABLE cdr")
    assert ok is False
    assert 'SELECT' in msg


def test_rejects_delete():
    ok, msg = _validate_report_sql("SELECT id FROM cdr; DELETE FROM cdr")
    assert ok is False
    assert 'delete' in msg.lower()


def test_rejects_insert():
    ok, msg = _validate_report_sql("INSERT INTO cdr VALUES (1)")
    assert ok is False


def test_rejects_update():
    ok, msg = _validate_report_sql("UPDATE cdr SET call_state='X'")
    assert ok is False


def test_rejects_comment_injection():
    ok, msg = _validate_report_sql("SELECT * FROM cdr -- drop table cdr")
    assert ok is False


def test_rejects_block_comment():
    ok, msg = _validate_report_sql("SELECT * FROM cdr /* injected */")
    assert ok is False


def test_case_insensitive():
    ok, msg = _validate_report_sql("SELECT * FROM cdr; DrOp TaBlE cdr")
    assert ok is False
