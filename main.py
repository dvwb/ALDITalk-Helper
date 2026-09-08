import os
import time
import json5
import sys
import io
import re
import random
import curl_cffi

# CONFIG LOADER
with open("config.json5", "r") as f:
    config = json5.load(f)

RUFNUMMER = config["RUFNUMMER"]
PASSWORT = config["PASSWORT"]

