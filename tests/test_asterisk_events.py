"""Tests for AsteriskEventsHandler — specifically the externalID boolean bug fix."""
import json
import pytest
from unittest.mock import MagicMock, patch


def _make_handler():
    from app.asterisk.AsteriskEventsHandler import AsteriskEventsHandler
    logger = MagicMock()
    cache = MagicMock()
    cdr = MagicMock()
    return AsteriskEventsHandler(logger, cache, cdr), logger, cache, cdr


def test_gen_status_link_includes_external_params_when_both_present():
    """__gen_status_link must append externalId/externalType when both are passed."""
    handler, _, _, _ = _make_handler()
    # Access private method via name mangling
    link = handler._AsteriskEventsHandler__gen_status_link(
        'call-1', 'COMPLETED', 'application', 'http://example.com/status',
        externalID='ext-123', externalType='Academy IVR'
    )
    assert 'externalId=ext-123' in link
    assert 'externalType=Academy+IVR' in link or 'externalType=Academy IVR' in link


def test_gen_status_link_excludes_external_params_when_missing():
    """__gen_status_link must not append external params when not passed."""
    handler, _, _, _ = _make_handler()
    link = handler._AsteriskEventsHandler__gen_status_link(
        'call-1', 'FAILED', 'unreachable', 'http://example.com/status'
    )
    assert 'externalId' not in link
    assert 'externalType' not in link


def test_get_channel_status_known_code():
    handler, _, _, _ = _make_handler()
    assert handler._AsteriskEventsHandler__get_channel_status('4') == 'COMPLETED'
    assert handler._AsteriskEventsHandler__get_channel_status('5') == 'BUSY'
    assert handler._AsteriskEventsHandler__get_channel_status('0') == 'FAILED'


def test_get_channel_status_unknown_code():
    handler, _, _, _ = _make_handler()
    assert handler._AsteriskEventsHandler__get_channel_status('99') == 'UNKNOWN'
