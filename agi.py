#!/usr/bin/env python3

import os
from asterisk.agi import AGI
from src.AppManager import AppManager
from src.AppDatabase import AppDatabase
from src.Config import Config
from src.IVR import IVR
from src.Logger import Logger
from src.Audio import Audio


# Get script directory
working_dir = os.path.dirname(os.path.realpath(__file__))

# Initialize Logger
logger = Logger(working_dir)

# Initialize the asterisk AGI
agi = AGI()

# Set maximum call time to 5 minutes
agi.set_autohangup(300)

# Initialize configuration parser
config = Config(working_dir, logger, 'app')

# Initialize the audio files parser
audio = Audio(config.get_audio_path())

# Initialize database
database = AppDatabase(config)

app_manager = AppManager(database, logger)

# Start the Interactive Voice Response
ivr = IVR(agi, logger, app_manager, audio)

try:
    ivr.run()
except Exception as e:
    logger.log_warning("Error executing IVR.py: {}".format(str(e)))
