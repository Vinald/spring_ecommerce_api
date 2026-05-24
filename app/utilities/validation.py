"""
Helper to validate request.form data against a marshmallow schema.

Usage in any API handler:
    from app.utilities.validation import validate_request
    from app.schemas.schemas import UserCreateSchema

    errors, data = validate_request(request.form, UserCreateSchema())
    if errors:
        return jsonify({'status': 'error', 'message': errors}), 400
    # use data['email'], data['role'] etc.
"""
from marshmallow import ValidationError


def validate_request(form_data, schema):
    """
    Validate a MultiDict (request.form) against a marshmallow schema.

    Returns (errors_dict_or_None, deserialized_data_or_None).
    On success: (None, data_dict)
    On failure: (error_messages_dict, None)
    """
    try:
        data = schema.load(form_data)
        return None, data
    except ValidationError as e:
        # Flatten multi-field error messages into a single readable string
        messages = e.messages
        flat = '; '.join(
            '{}: {}'.format(field, ', '.join(msgs) if isinstance(msgs, list) else str(msgs))
            for field, msgs in messages.items()
        )
        return flat, None
