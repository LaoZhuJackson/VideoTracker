# coding: utf-8
import time
from functools import partial

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QApplication

from qfluentwidgets import SplashScreen, setThemeColor, FlyoutView, Flyout
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
        self.current_pivot_route = None
        self.support_widget = None
        self.initWindow()

        # TODO: create sub interface
        self.browserInterface = BrowserWindow('Browser Window', self)
        self.settingInterface = SettingInterface(self)

        self.connectSignalToSlot()

        # add items to navigation interface
        self.initNavigation()

    def connectSignalToSlot(self):
        signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)
        self.pivot.currentItemChanged.connect(self.onPivotChanged)

    def initNavigation(self):
        # TODO: add navigation items
        self.addSubInterface(self.browserInterface, FIF.GLOBE, "browserInterface")
        self.addSubInterface(self.settingInterface, FIF.SETTING, self.tr('Settings'))
        self.support_widget = self.pivot.addItem("avatar", FIF.HEART, onClick=self.on_support)
        # 设置初始选中
        self.pivot.setCurrentItem(self.browserInterface.objectName())
        self.current_pivot_route = self.pivot.currentRouteKey()
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
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)
        self.show()
        QApplication.processEvents()

    def onPivotChanged(self):
        self.current_pivot_route = self.pivot.currentRouteKey()

    def on_support(self):
        def close():
            w.close()
            self.pivot.setCurrentItem(self.stackedWidget.currentWidget().objectName())

        view = FlyoutView(
            title="赞助作者",
            content="如果这个助手帮助到你，可以考虑赞助作者一杯奶茶(>ω･* )ﾉ",
            image="asset/support.jpg",
            isClosable=True,
        )
        view.widgetLayout.insertSpacing(1, 5)
        view.widgetLayout.addSpacing(5)

        w = Flyout.make(view, self.support_widget, self)
        view.closed.connect(close)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'splashScreen'):
            self.splashScreen.resize(self.size())

    def closeEvent(self, a0):
        # 调用孩子的closeEvent关闭webview进程
        self.browserInterface.closeEvent(a0)
        super().closeEvent(a0)
