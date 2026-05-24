"""
Tests for AsteriskEventsHandler.

Covers two fixes from PR #30:
  1. externalID/externalType boolean bug — the original condition
     `if 'externalID' and 'externalType' in optional_params` was always True
     because 'externalID' is a non-empty string (truthy). Both keys must be
     checked explicitly with `in optional_params`.

  2. Status code mapping — __get_channel_status must return 'UNKNOWN' for
     codes not in the STATUS_CODES dict instead of raising KeyError.
"""
from unittest.mock import MagicMock


def _make_handler():
    """Build an AsteriskEventsHandler with mocked dependencies."""
    from app.asterisk.AsteriskEventsHandler import AsteriskEventsHandler
    return AsteriskEventsHandler(MagicMock(), MagicMock(), MagicMock())


def test_status_link_includes_external_params_when_both_provided():
    """
    When both externalID and externalType are in optional_params,
    the generated link must include both as query parameters.
    """
    handler = _make_handler()
    link = handler._AsteriskEventsHandler__gen_status_link(
        'call-1', 'COMPLETED', 'application', 'http://example.com/status',
        externalID='ext-123', externalType='Academy IVR'
    )
    assert 'externalId=ext-123' in link
    assert 'externalType=' in link


def test_status_link_excludes_external_params_when_not_provided():
    """
    When optional params are absent, the link must NOT include externalId/Type.
    Before the fix, the old boolean condition always appended them, which
    would cause a KeyError inside __gen_status_link.
    """
    handler = _make_handler()
    link = handler._AsteriskEventsHandler__gen_status_link(
        'call-1', 'FAILED', 'unreachable', 'http://example.com/status'
    )
    assert 'externalId' not in link
    assert 'externalType' not in link


def test_known_status_codes_mapped_correctly():
    """Status codes 0, 3, 4, 5, 8 must map to their defined string values."""
    handler = _make_handler()
    assert handler._AsteriskEventsHandler__get_channel_status('4') == 'COMPLETED'
    assert handler._AsteriskEventsHandler__get_channel_status('5') == 'BUSY'
    assert handler._AsteriskEventsHandler__get_channel_status('3') == 'NO_ANSWER'
    assert handler._AsteriskEventsHandler__get_channel_status('0') == 'FAILED'
    assert handler._AsteriskEventsHandler__get_channel_status('8') == 'FAILED'


def test_unknown_status_code_returns_unknown_not_keyerror():
    """
    An unrecognised status code must return 'UNKNOWN'.
    Before the fix dict[] access would raise KeyError; now uses .get().
    """
    handler = _make_handler()
    assert handler._AsteriskEventsHandler__get_channel_status('99') == 'UNKNOWN'
    assert handler._AsteriskEventsHandler__get_channel_status('') == 'UNKNOWN'
