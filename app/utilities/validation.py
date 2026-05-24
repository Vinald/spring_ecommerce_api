"""
Helper to validate request.form / request.args against a marshmallow schema.

ADDED: centralised validation helper used by all API handlers. Previously each
handler read fields directly from request.form — a missing key raised KeyError
which Flask caught and returned as HTTP 500 with no useful message for the
caller. This helper returns a human-readable error string on failure so the
handler can return HTTP 400 immediately.

Usage:
    from app.utilities.validation import validate_request
    from app.schemas.schemas import UserCreateSchema

    errors, data = validate_request(request.form, UserCreateSchema())
    if errors:
        return jsonify({'status': 'error', 'message': errors}), 400
    # Safe to use data['email'], data['role'] etc.
"""
from marshmallow import ValidationError


def validate_request(form_data, schema):
    """
    Validate a MultiDict (request.form or request.args) against a marshmallow schema.

    Returns:
        (None, data_dict)        on success — data is deserialised and type-safe
        (error_string, None)     on failure — error_string is human-readable
    """
    try:
        data = schema.load(form_data)
        return None, data
    except ValidationError as e:
        # Flatten per-field error lists into a single semicolon-separated string
        # so callers can return it directly in a JSON error response.
        messages = e.messages
        flat = '; '.join(
            '{}: {}'.format(field, ', '.join(msgs) if isinstance(msgs, list) else str(msgs))
            for field, msgs in messages.items()
        )
        return flat, None
