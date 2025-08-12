# coding: utf-8
from pathlib import Path

# change DEBUG to False if you want to compile the code to exe
DEBUG = "__compiled__" not in globals()


YEAR = 2025
AUTHOR = "Laozhu"
VERSION = "v0.0.1"
APP_NAME = "VideoTracker"
HELP_URL = "https://qfluentwidgets.com"
REPO_URL = "https://github.com/LaoZhuJackson/VideoTracker"
FEEDBACK_URL = "https://github.com/LaoZhuJackson/VideoTracker/issues"
DOC_URL = "https://qfluentwidgets.com/"

CONFIG_FOLDER = Path('AppData').absolute()
CONFIG_FILE = CONFIG_FOLDER / "config.json"
