#!/usr/bin/env python3
"""
Application entry point.

CHANGED: all routes have been moved out of this file into Flask Blueprints:
  app/blueprints/ivr.py  — telephony routes (/call.initiate, /ivr/*, /health)
  app/blueprints/api.py  — authenticated REST routes (/api/*)

This file now contains only the application factory (create_app) and the
startup block. Benefits:
  - Each domain is independently readable and testable.
  - Blueprints can be mounted at different URL prefixes easily.
  - Unit tests can call create_app() without side effects.
"""
import os
from datetime import timedelta

from flask import Flask, jsonify
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
    app = Flask(__name__)

    # ── JWT ───────────────────────────────────────────────────────────────
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
    _frontend_origin = os.environ.get("FRONTEND_ORIGIN", "http://localhost:8080")
    CORS(app, origins=[_frontend_origin])

    # ── Rate limiting — backed by Redis ───────────────────────────────────
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
    # Inject dependencies then register — keeps blueprints free of global imports.
    init_ivr_blueprint(core, queue, asterisk_ari, core.asterisk_events_handler, core.database, core.logger)
    init_api_blueprint(core, queue, asterisk_ari, cdr_manager, peer_manager, Session, core.logger)

    app.register_blueprint(ivr_bp)
    app.register_blueprint(api_bp)

    # Apply rate limits to specific routes by endpoint name
    limiter.limit("30 per minute")(app.view_functions['ivr.initiate_call'])
    limiter.limit("10 per minute")(app.view_functions['api.login'])
    limiter.exempt(app.view_functions['ivr.health'])
    limiter.exempt(app.view_functions['ivr.process_queue'])
    limiter.exempt(app.view_functions['ivr.asterisk_events'])

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
