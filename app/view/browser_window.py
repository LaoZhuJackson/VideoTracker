import ctypes
import re
import sys
from ctypes import wintypes

from PyQt5.QtCore import QUrl, Qt, pyqtSlot, QTimer, QEvent
from PyQt5.QtMultimedia import QMediaContent
from PyQt5.QtWidgets import QFrame

from app.common.config import config
from app.common.signal_bus import signalBus
from app.modules.webview.webview_manager import WebView2Widget
# from app.repackge.my_web_engine_view import SinglePageWebEngineView
from app.ui.BrowserWindow import Ui_Browser
from qfluentwidgets import FluentIcon as FIF, InfoBar, InfoBarPosition, SimpleCardWidget


class BrowserWindow(QFrame, Ui_Browser):
    def __init__(self, text, parent=None):
        super().__init__()

        self.setupUi(self)
        self.setObjectName(text.replace(' ', '-'))
        self.parent = parent

        self.can_back = False
        self.can_forward = False

        self.default_url = config.defaultPageUrl.value

        self._initManager()
        self._initWidget()
        self._connect_to_slot()

    def _initManager(self):
        # 创建WebView组件
        # self.web_view = SinglePageWebEngineView()
        pass

    def _initWidget(self):
        self.ToolButton_back.setIcon(FIF.PAGE_LEFT)
        self.ToolButton_forward.setIcon(FIF.PAGE_RIGHT)
        self.ToolButton_refresh.setIcon(FIF.SYNC)
        self.ToggleToolButton_pin.setIcon(FIF.PIN)
        self.ToolButton_refresh.setEnabled(False)

        self.ToolButton_refresh.setShortcut("F5")  # 标准刷新快捷键
        self.SearchLineEdit.searchButton.setShortcut("Return")
        self.ToolButton_back.setShortcut("Alt+Left")  # 浏览器标准后退快捷键
        self.ToolButton_forward.setShortcut("Alt+Right")  # 浏览器标准前进快捷键

        self.SearchLineEdit.setPlaceholderText("输入网址")
        # self.SearchLineEdit.installEventFilter(self)
        self.web_view = WebView2Widget(self)
        self.gridLayout.addWidget(self.web_view, 1, 0, 1, 5)
        self.web_view.start_webview(url=self.default_url)

    def _connect_to_slot(self):
        # 连接信号，在页面加载完成后更新地址栏
        # self.web_view.urlChanged.connect(self._update_url_display)
        # self.web_view.loadFinished.connect(self.check_for_video)

        self.SearchLineEdit.searchSignal.connect(self.on_search_click)

        # 连接信号
        self.web_view.history_state_changed.connect(self.update_tool_button_enable)
        self.web_view.navigation_completed.connect(self._update_url_display)

        self.ToolButton_back.clicked.connect(self.web_view.go_back)
        self.ToolButton_forward.clicked.connect(self.web_view.go_forward)
        self.ToolButton_refresh.clicked.connect(self.web_view.reload)

        self.ToggleToolButton_pin.toggled.connect(self.toggle_pin)

        self.ToolButton_back.setEnabled(False)
        self.ToolButton_forward.setEnabled(False)

    def _update_url_display(self,url):
        """页面加载完成后更新地址栏显示"""
        # 获取最终解析的URL
        # final_url = self.web_view.url()
        # 显示URL
        # display_url = final_url.toString()
        self.ToolButton_refresh.setEnabled(True)
        self.SearchLineEdit.setText(url)

    def on_webview_initialized(self):
        """WebView2 初始化完成后再加载页面"""
        if self.default_url:
            self.web_view.load(self.default_url)  # 加载网页

    def on_search_click(self, url):
        url = url.strip()
        if not url:
            return
        if '.' not in url and 'localhost' not in url:
            url = 'https://www.baidu.com/s?ie=UTF-8&wd=' + url
        elif not re.match(r'^https?://', url, re.I):
            url = 'https://' + url
        self.web_view.load(url)

    def update_tool_button_enable(self, can_go_back=None, can_go_forward=None):
        """更新工具栏按钮状态"""
        self.ToolButton_back.setEnabled(can_go_back)
        self.ToolButton_forward.setEnabled(can_go_forward)

    def toggle_pin(self, checked):
        try:
            if sys.platform == "win32":
                # 使用Win32 API避免窗口重建
                HWND = wintypes.HWND(int(self.parent.winId()))

                if checked:
                    # 正确设置窗口置顶
                    ctypes.windll.user32.SetWindowPos(
                        HWND,
                        wintypes.HWND(-1),  # HWND_TOPMOST (-1)
                        0, 0, 0, 0,
                        0x0001 | 0x0002  # SWP_NOMOVE | SWP_NOSIZE
                    )
                    # 显示成功通知
                    InfoBar.success(
                        title='已置顶',
                        content="窗口将保持在最前面",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self.parent
                    )
                else:
                    # 取消置顶
                    ctypes.windll.user32.SetWindowPos(
                        HWND,
                        wintypes.HWND(-2),  # HWND_NOTOPMOST (-2)
                        0, 0, 0, 0,
                        0x0001 | 0x0002 | 0x0040  # SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
                    )
                    # 显示信息通知
                    InfoBar.info(
                        title='取消置顶',
                        content="窗口恢复正常层级",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self.parent
                    )
            else:
                # 非Windows系统使用原方法（会有短暂消失）
                self._toggle_pin_fallback(checked)

        except Exception as e:
            print(f"置顶切换出错: {str(e)}")
            self._toggle_pin_fallback(checked)

    def _toggle_pin_fallback(self, checked):
        """回退方法：使用PyQt原生方法"""
        # 保存当前窗口状态
        was_maximized = self.parent.isMaximized()
        geometry = self.parent.geometry()

        if checked:
            self.parent.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        else:
            self.parent.setWindowFlag(Qt.WindowStaysOnTopHint, False)

        # 重新显示并恢复状态
        self.parent.show()

        if was_maximized:
            self.parent.showMaximized()
        else:
            self.parent.setGeometry(geometry)
            self.parent.showNormal()

        # 确保窗口在前台
        self.parent.activateWindow()
        self.parent.raise_()

    @pyqtSlot()
    async def check_for_video(self):
        js_code = """
            (function() {
                var video = document.querySelector("video");
                if (video) {
                    if (video.src) {
                        return video.src;
                    } else if (video.querySelector("source")) {
                        return video.querySelector("source").src;
                    }
                }
                return null;
            })();
        """
        url = await self.web_view.run_js(js_code)
        self.handle_video_url(url)

    def handle_video_url(self, url):
        if url:
            print("检测到视频地址：", url)
            signalBus.getVideoUrl.emit(url)
        else:
            print("未检测到视频标签")

    def closeEvent(self, a0):
        self.web_view.cleanup()
        super().closeEvent(a0)



