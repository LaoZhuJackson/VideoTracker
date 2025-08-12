# coding: utf-8
import time

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QApplication

from qfluentwidgets import SplashScreen, setThemeColor
from qfluentwidgets import FluentIcon as FIF

from .browser_window import BrowserWindow
from .setting_interface import SettingInterface
from ..common.config import config
from ..common.signal_bus import signalBus
from ..common import resource
from ..repackge.my_main_window import MyMainWindow


class MainWindow(MyMainWindow):

    def __init__(self):
        super().__init__()
        self.initWindow()

        # TODO: create sub interface
        self.browserInterface = BrowserWindow('Browser Window', self)
        self.settingInterface = SettingInterface(self)

        self.connectSignalToSlot()

        # add items to navigation interface
        self.initNavigation()

    def connectSignalToSlot(self):
        signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)

    def initNavigation(self):
        # TODO: add navigation items
        self.addSubInterface(self.browserInterface, FIF.GLOBE, "browserInterface")

        # add custom widget to bottom
        self.addSubInterface(
            self.settingInterface, FIF.SETTING, self.tr('Settings'))
        # 设置初始选中
        self.pivot.setCurrentItem(self.browserInterface.objectName())
        self.stackedWidget.setCurrentWidget(self.browserInterface)

        self.splashScreen.finish()

    def initWindow(self):
        self.resize(1107, 780)
        self.setMinimumWidth(760)
        self.setWindowIcon(QIcon(':/app/images/logo.png'))
        self.setWindowTitle('VideoTracker')

        self.setCustomBackgroundColor(QColor(240, 244, 249), QColor(32, 32, 32))
        self.setMicaEffectEnabled(config.get(config.micaEnabled))
        setThemeColor("#2D527C")

        # create splash screen
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        desktop = QApplication.primaryScreen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
        self.show()
        QApplication.processEvents()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'splashScreen'):
            self.splashScreen.resize(self.size())

    def closeEvent(self, a0):
        # 调用孩子的closeEvent关闭webview进程
        self.browserInterface.closeEvent(a0)
        super().closeEvent(a0)
