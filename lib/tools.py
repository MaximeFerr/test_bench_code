import json
import os
import sys
import time
import math
from datetime import datetime
from typing import cast, Any

import serial.serialutil
import pyvisa as visa
import numpy as np
import matplotlib.pyplot as plt

class TOOL:
    """
    Class for various utility functions.
    """

    def find_json_files(folder):
        """
        Recursively finds all JSON files in the specified folder and its subfolders.
        Useful only for testing purposes to easily load configuration files without hardcoding paths.
        """

        json_files = []
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith('.json'):
                    json_files.append(os.path.relpath(os.path.join(root, file), "./"))
        return json_files