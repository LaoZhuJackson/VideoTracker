# coding:utf-8
import sys
from enum import Enum

from PyQt5.QtCore import QLocale
from qfluentwidgets import (qconfig, QConfig, ConfigItem, OptionsConfigItem, BoolValidator,
                            OptionsValidator, Theme, FolderValidator, ConfigSerializer)

from .setting import CONFIG_FILE

class Language(Enum):
    """ Language enumeration """

    CHINESE_SIMPLIFIED = QLocale(QLocale.Chinese, QLocale.China)
    CHINESE_TRADITIONAL = QLocale(QLocale.Chinese, QLocale.HongKong)
    ENGLISH = QLocale(QLocale.English)
    AUTO = QLocale()


class LanguageSerializer(ConfigSerializer):
    """ Language serializer """

    def serialize(self, language):
        return language.value.name() if language != Language.AUTO else "Auto"

    def deserialize(self, value: str):
        return Language(QLocale(value)) if value != "Auto" else Language.AUTO


def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000


class Config(QConfig):
    """ Config of application """

    # TODO: ADD YOUR CONFIG GROUP HERE


    # browser window
    defaultPageUrl = ConfigItem("browser", "defaultPageUrl", "https://www.bilibili.com")
    forward_second = OptionsConfigItem("browser", "forward_second", 3, OptionsValidator([1, 3, 5, 10]))
    backward_second = OptionsConfigItem("browser", "backward_second", 3, OptionsValidator([1, 3, 5, 10]))

    # main window
    micaEnabled = ConfigItem("MainWindow", "MicaEnabled", isWin11(), BoolValidator())
    dpiScale = OptionsConfigItem(
        "MainWindow", "DpiScale", 'Auto', OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True)
    language = OptionsConfigItem(
        "MainWindow", "Language", Language.AUTO, OptionsValidator(Language), LanguageSerializer(), restart=True)

    # software update
    checkUpdateAtStartUp = ConfigItem("Update", "CheckUpdateAtStartUp", True, BoolValidator())
    # setting interface
    playVideoShortcut = ConfigItem("Shortcut", "playVideoShortcut", "Ctrl+Alt+P")
    forwardVideoShortcut = ConfigItem("Shortcut", "forwardVideoShortcut", "Ctrl+Alt+Right")
    backwardVideoShortcut = ConfigItem("Shortcut", "backwardVideoShortcut", "Ctrl+Alt+Left")
    fullscreenShortcut = ConfigItem("Shortcut", "fullscreenShortcut", "Ctrl+Alt+F")
    volumeUpShortcut = ConfigItem("Shortcut", "volumeUpShortcut", "Ctrl+Alt+Up")
    volumeDownShortcut = ConfigItem("Shortcut", "volumeDownShortcut", "Ctrl+Alt+Down")


config = Config()
config.themeMode.value = Theme.AUTO
qconfig.load(str(CONFIG_FILE.absolute()), config)