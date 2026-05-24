"""
Request validation schemas for all API endpoints.

ADDED: Previously all API handlers read from request.form with no schema
validation. A missing required field raised KeyError which Flask returned
as an unhandled HTTP 500. These marshmallow schemas enforce required fields,
types, and value constraints at the request boundary — returning HTTP 400
with a clear message before any business logic runs.

Each schema maps to one API handler. Use validate_request() from
app/utilities/validation.py to apply a schema to request.form or request.args.
"""
from marshmallow import Schema, fields, validate, validates_schema, ValidationError


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginSchema(Schema):
    # Both fields are required — missing either would previously cause KeyError.
    username = fields.Email(required=True, error_messages={'required': 'username is required'})
    password = fields.Str(required=True, validate=validate.Length(min=1))


class ProfileUpdateSchema(Schema):
    oldPassword = fields.Str(required=True, validate=validate.Length(min=1))
    # Password complexity enforced here instead of duplicating the regex in Profile.py.
    password = fields.Str(
        required=True,
        validate=validate.Regexp(
            r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[a-zA-Z]).{8,}$',
            error='Password must be at least 8 characters with uppercase, lowercase, and a digit.'
        )
    )


# ── Users ─────────────────────────────────────────────────────────────────────

class UserCreateSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
    # Role is constrained to known values — prevents arbitrary role escalation.
    role = fields.Str(required=True, validate=validate.OneOf(['admin', 'user']))


class UserUpdateSchema(Schema):
    id = fields.Int(required=True, validate=validate.Range(min=1))
    email = fields.Email(required=True)
    password = fields.Str(load_default='')  # blank = keep existing password
    role = fields.Str(required=True, validate=validate.OneOf(['admin', 'user']))


class UserDeleteSchema(Schema):
    id = fields.Int(required=True, validate=validate.Range(min=1))


# ── Applications ──────────────────────────────────────────────────────────────

class AppCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=40))
    phone = fields.Str(load_default='', validate=validate.Length(max=40))
    # voice_url and status_url must be valid URLs — prevents saving garbage that
    # would silently break call flows later.
    voice_url = fields.Url(required=True)
    status_url = fields.Url(required=True)
    caller_id = fields.Str(load_default='', validate=validate.Length(max=40))
    toll_free = fields.Str(load_default='', validate=validate.Length(max=40))


class AppUpdateSchema(Schema):
    id = fields.Int(required=True, validate=validate.Range(min=1))
    name = fields.Str(required=True, validate=validate.Length(min=1, max=40))
    phone = fields.Str(load_default='', validate=validate.Length(max=40))
    voice_url = fields.Url(required=True)
    status_url = fields.Url(required=True)
    caller_id = fields.Str(load_default='', validate=validate.Length(max=40))
    toll_free = fields.Str(load_default='', validate=validate.Length(max=40))


class AppDeleteSchema(Schema):
    id = fields.Int(required=True, validate=validate.Range(min=1))


# ── Reports ───────────────────────────────────────────────────────────────────

_RECURRENCES = ['daily', 'weekly', 'monthly']
_DAYS_OF_WEEK = ['0', '1', '2', '3', '4', '5', '6']


class ReportCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    type = fields.Int(required=True, validate=validate.Range(min=1))
    scheduled = fields.Str(required=True, validate=validate.OneOf(['true', 'false']))
    recurrence = fields.Str(required=True, validate=validate.OneOf(_RECURRENCES))
    time = fields.Str(required=True)
    day = fields.Str(required=True, validate=validate.OneOf(_DAYS_OF_WEEK + ['']))
    to = fields.Str(required=True, validate=validate.Length(min=1))
    cc = fields.Str(load_default='')

    @validates_schema
    def validate_weekly_day(self, data, **kwargs):
        """
        FIXED (Copilot review): day='' was accepted for all recurrences.
        If recurrence='weekly' and day='', _build_cron_expression() would
        produce an invalid cron expression like '30 09 * * ' which
        __reload_reports_cron_tab() would still write (passes char allowlist).
        Now enforced: weekly recurrence requires an explicit day 0-6.
        """
        if data.get('recurrence') == 'weekly' and data.get('scheduled') == 'true':
            if data.get('day', '') == '':
                raise ValidationError(
                    'day is required (0=Sun … 6=Sat) when recurrence is weekly',
                    field_name='day'
                )


class ReportUpdateSchema(ReportCreateSchema):
    # id is required on update but not on create.
    id = fields.Int(required=True, validate=validate.Range(min=1))


# ── Report Types ──────────────────────────────────────────────────────────────

class ReportTypeCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    # Minimum length of 7 = len("SELECT ") — anything shorter cannot be a valid SELECT.
    sql = fields.Str(required=True, validate=validate.Length(min=7))


class ReportTypeUpdateSchema(ReportTypeCreateSchema):
    # FIXED (Copilot review): added id field so ReportTypes.__put() can validate
    # the id param instead of doing bare int(request.form['id']).
    id = fields.Int(required=True, validate=validate.Range(min=1))


class ReportTypeDeleteSchema(Schema):
    # FIXED (Copilot review): added so ReportTypes.__delete() can validate the
    # id query param instead of doing bare int(request.args.get('id')).
    id = fields.Int(required=True, validate=validate.Range(min=1))
