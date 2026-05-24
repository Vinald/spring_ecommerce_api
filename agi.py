#!/usr/bin/env python3
"""
Asterisk Gateway Interface (AGI) entry point.

Called by Asterisk for every inbound/outbound call. Sets up the IVR
and runs the VXML call flow.

CHANGED: Apps now receives Session (sessionmaker) instead of a Database
instance, consistent with the dual DB layer consolidation in core.py.
"""
from asterisk.agi import AGI
from app.api.Apps import Apps
from app.core import logger, config, audio_path, max_call_time, dates_audio_path, Session
from app.ivr.Audio import Audio
from app.ivr.IVR import IVR

agi = AGI()
agi.set_autohangup(max_call_time)

audio = Audio(audio_path, dates_audio_path)

# CHANGED: was Apps(Database(config), logger) — now passes Session (sessionmaker).
app_manager = Apps(Session, logger)

ivr = IVR(agi, logger, app_manager, audio)

try:
    ivr.run()
except Exception as e:
    logger.log_warning("Error executing IVR: {}".format(str(e)))
