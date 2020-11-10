#!/usr/bin/env python3

from asterisk.agi import AGI
from app.api.Apps import Apps
from app.core import logger, config, audio_path, max_call_time, dates_audio_path
from app.ivr.Audio import Audio
from app.ivr.IVR import IVR
from app.utilities.Database import Database

# Initialize the asterisk AGI
agi = AGI()

# Set maximum call time to 5 minutes
agi.set_autohangup(max_call_time)

# Initialize the audio files parser
audio = Audio(audio_path, dates_audio_path)

# Initialize database
database = Database(config)

app_manager = Apps(database, logger)

# Start the Interactive Voice Response
ivr = IVR(agi, logger, app_manager, audio)
ivr.run()
