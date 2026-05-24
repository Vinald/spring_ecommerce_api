"""
Flask Blueprints package.

ADDED: Previously all 13 routes lived in run.py, mixing telephony, event
handling, and REST API concerns in one 160-line file. Routes are now split
into two focused blueprints:

  ivr_bp  (app/blueprints/ivr.py)
      /health          — liveness probe for Docker / load balancers
      /call.initiate   — external apps trigger outbound calls here
      /ivr/queue       — internal: drain queued calls (127.0.0.1 only)
      /ivr/events      — internal: Asterisk AMI event callbacks (127.0.0.1 only)

  api_bp  (app/blueprints/api.py)
      /api/login              — JWT login
      /api/dashboard-stats    — system metrics (admin only)
      /api/charts             — CDR chart data
      /api/apps               — CRUD for IVR applications
      /api/reports            — CRUD for scheduled reports
      /api/report-types       — CRUD for report SQL templates
      /api/user               — user management (admin only)
      /api/profile            — password change for current user
      /api/roles              — role list
      /api/logs               — user log files

Each blueprint receives its dependencies via an init_*_blueprint() injector
called from create_app() in run.py — no global imports from core inside
blueprint files, making them independently testable.
"""
