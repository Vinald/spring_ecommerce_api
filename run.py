#!/usr/bin/env python3
"""
Application entry point — application factory pattern.

CHANGED: Previously all 13 routes lived directly in this file (~160 lines),
mixing telephony, event handling, and REST API concerns. This made the file
hard to read and impossible to unit-test routes in isolation.

Routes are now in two Flask Blueprints:
  app/blueprints/ivr.py  — /health, /call.initiate, /ivr/queue, /ivr/events
  app/blueprints/api.py  — all /api/* routes

This file now contains only:
  1. create_app() — application factory (testable, importable without side effects)
  2. The startup block (if __name__ == '__main__')

Other changes in this file vs the original:
  - JWT secret-key is validated at startup — raises RuntimeError if blank
  - CORS restricted to FRONTEND_ORIGIN env var instead of allowing all origins
  - Flask-Limiter added: 30/min on /call.initiate, 10/min on /api/login
  - In-memory logged_in_users dict removed — was a memory leak that broke
    multi-worker deployments; JWT lookup now always queries the DB
  - debug=False in production
"""
import os
from datetime import timedelta

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.orm import scoped_session

from app import core
from app.blueprints.ivr import ivr_bp, init_ivr_blueprint
from app.blueprints.api import api_bp, init_api_blueprint
from app.core import asterisk_ari, cdr_manager, peer_manager, Session
from app.manager.QueueManager import QueueManager
from app.models.models import User


def create_app():
    """
    Application factory.
    Returns a fully configured Flask app.
    Called by the startup block below and by the test suite.
    """
    app = Flask(__name__)

    # ── JWT ───────────────────────────────────────────────────────────────
    # CHANGED: was read without checking — an empty secret means any token
    # can be forged. Fail fast at startup so the problem is obvious.
    _secret_key = core.secret_key
    if not _secret_key:
        raise RuntimeError(
            "JWT secret-key is empty. Set a strong value in config.json "
            "under [core] secret-key."
        )
    app.config["JWT_SECRET_KEY"] = _secret_key
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=3)
    jwt = JWTManager(app)

    # ── CORS ──────────────────────────────────────────────────────────────
    # CHANGED: was CORS(app) — allows any origin. Now restricted to the
    # frontend origin configured via the FRONTEND_ORIGIN environment variable.
    _frontend_origin = os.environ.get("FRONTEND_ORIGIN", "http://localhost:8080")
    CORS(app, origins=[_frontend_origin])

    # ── Rate limiting — backed by Redis ───────────────────────────────────
    # ADDED: /call.initiate had no rate limit — a valid token could flood the
    # queue. /api/login had no brute-force protection.
    _redis_host = core.config.set_section('redis').get('host', 'localhost')
    _redis_port = core.config.set_section('redis').get('port', '6379')
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri="redis://{}:{}/1".format(_redis_host, _redis_port),
        default_limits=["200 per minute"],
    )

    # ── JWT user loader ───────────────────────────────────────────────────
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        return user.id

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        # CHANGED: was caching users in a logged_in_users dict — grew forever,
        # broke multi-worker deployments. Now always queries the DB via the
        # SQLAlchemy scoped session.
        identity = jwt_data["sub"]
        s_session = scoped_session(Session)
        db_session = s_session()
        try:
            return db_session.query(User).filter_by(id=identity).one_or_none()
        except Exception as e:
            core.logger.log_info(f"JWT user lookup DB error: {str(e)}")
            db_session.rollback()
            return None

    # ── Shared services ───────────────────────────────────────────────────
    core.database.reconnect()
    queue = QueueManager(core.cache)

    # ── Register blueprints ───────────────────────────────────────────────
    # ADDED: blueprints receive dependencies via injectors so they have no
    # direct imports from core — keeping them independently testable.
    init_ivr_blueprint(
        core, queue, asterisk_ari,
        core.asterisk_events_handler, core.database, core.logger
    )
    init_api_blueprint(
        core, queue, asterisk_ari,
        cdr_manager, peer_manager, Session, core.logger
    )

    app.register_blueprint(ivr_bp)
    app.register_blueprint(api_bp)

    # Apply specific rate limits by blueprint endpoint name.
    limiter.limit("30 per minute")(app.view_functions['ivr.initiate_call'])
    limiter.limit("10 per minute")(app.view_functions['api.login'])
    limiter.exempt(app.view_functions['ivr.health'])
    limiter.exempt(app.view_functions['ivr.process_queue'])
    limiter.exempt(app.view_functions['ivr.asterisk_events'])

    return app


app = create_app()

if __name__ == '__main__':
    # CHANGED: was debug=True which exposes the Werkzeug debugger in production.
    app.run(host='0.0.0.0', port=5000, debug=False)
