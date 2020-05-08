#!/home/arksnorman/Projects/ivr/venv/bin/python

import asterisk.agi
import os
from src.Config import Config
from src.IVR import IVR
from src.Logger import Logger
from src.Audio import Audio


# Get script directory
working_dir = os.path.dirname(os.path.realpath(__file__))

# Initialize Logger
logger = Logger(working_dir)

# Initialize the asterisk AGI
agi = asterisk.agi.AGI()

# Set maximum call time to 5 minutes
agi.set_autohangup(300)

# Initialize configuration parser
config = Config(working_dir, logger, 'motech')

# Initialize the audio files parser
audio = Audio(config.get_audio_path())

# Define the starting voice URL of the application
base_link = config.get_starting_url()

# Start the Interactive Voice Response
ivr = IVR(base_link, agi, logger, audio)
ivr.run()
