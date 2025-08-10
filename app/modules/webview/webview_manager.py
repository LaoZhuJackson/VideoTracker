import sys
import subprocess
import time
import ctypes
from ctypes import wintypes
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import QTimer, Qt, QRect, pyqtSignal, QEvent

# 需要提前 pip install psutil（可选）
try:
    import psutil
except Exception:
    psutil = None

CHILD_PY = "app/modules/webview/child_webview.py"  # 子进程脚本路径（相对于当前工作目录）
WEBVIEW_TITLE = "MyEmbeddedWebView2Window_12345"  # 子窗口标题（要唯一，便于查找）
TARGET_URL = "https://www.bilibili.com/video/BV1MStbzSEor"

# Win32 常量
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
GWL_STYLE = -16
WS_VISIBLE = 0x10000000
WS_CHILD = 0x40000000
WS_OVERLAPPEDWINDOW = 0x00CF0000

user32 = ctypes.WinDLL("user32", use_last_error=True)

FindWindowW = user32.FindWindowW
FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
FindWindowW.restype = wintypes.HWND

SetParent = user32.SetParent
SetParent.argtypes = [wintypes.HWND, wintypes.HWND]
SetParent.restype = wintypes.HWND

SetWindowLongW = user32.SetWindowLongW
SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
SetWindowLongW.restype = ctypes.c_long

GetWindowLongW = user32.GetWindowLongW
GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
GetWindowLongW.restype = ctypes.c_long

SetWindowPos = user32.SetWindowPos
SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
SetWindowPos.restype = wintypes.BOOL

IsWindow = user32.IsWindow
IsWindow.argtypes = [wintypes.HWND]
IsWindow.restype = wintypes.BOOL


class WebView2Widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.parent = parent
        self.child_proc = None
        self.child_hwnd = None
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(100)
        self._poll_timer.timeout.connect(self._poll_embed)

    def setup_ui(self):
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        # 创建用于嵌入的黑色区域
        self.embed_area = QWidget(self)
        self.layout().addWidget(self.embed_area)
        self.embed_area.hide()  # 刚开始隐藏，避免闪

    def start_webview(self, title=WEBVIEW_TITLE, url="https://www.baidu.com"):
        """启动并嵌入WebView"""
        if self.child_proc and self.child_proc.poll() is None:
            return  # 已运行

        host_hwnd = int(self.embed_area.winId())  # 获取 embed_area HWND
        cmd = [sys.executable, CHILD_PY, title, url]
        self.child_proc = subprocess.Popen(cmd)
        self._poll_timer.start()

    def close_webview(self):
        """关闭WebView"""
        if self.child_proc and self.child_proc.poll() is None:
            self.child_proc.terminate()
            try:
                self.child_proc.wait(timeout=3)
            except Exception:
                self.child_proc.kill()
        self.child_proc = None
        self.child_hwnd = None

    def _poll_embed(self):
        if self.child_proc and self.child_proc.poll() is not None:
            self._poll_timer.stop()
            self.child_proc = None
            return

        hwnd = FindWindowW(None, WEBVIEW_TITLE)
        if hwnd:
            self._poll_timer.stop()
            self.child_hwnd = hwnd
            self._embed_hwnd(hwnd)
            self.embed_area.show()  # 嵌入完成再显示

    def _embed_hwnd(self, child_hwnd):
        host_hwnd = int(self.embed_area.winId())

        # 修改窗口样式
        style = GetWindowLongW(child_hwnd, GWL_STYLE)
        new_style = (style & ~WS_OVERLAPPEDWINDOW) | WS_CHILD | WS_VISIBLE
        SetWindowLongW(child_hwnd, GWL_STYLE, new_style)

        # 设置父窗口
        SetParent(child_hwnd, host_hwnd)

        # 调整初始大小
        self.resize_child_window()
        self.embed_area.installEventFilter(self)

    def resize_child_window(self):
        """调整子窗口大小匹配嵌入区域"""
        if self.child_hwnd and IsWindow(self.child_hwnd):
            dpr = self.embed_area.devicePixelRatioF()
            width = int(self.embed_area.width() * dpr)
            height = int(self.embed_area.height() * dpr)
            SetWindowPos(
                self.child_hwnd, 0,
                0, 0, width, height,
                SWP_NOZORDER | SWP_NOACTIVATE
            )

    def eventFilter(self, source, event):
        if source is self.embed_area and event.type() == QEvent.Resize:
            self.resize_child_window()
        return super().eventFilter(source, event)

    def showEvent(self, event):
        super().showEvent(event)
        # 在控件首次显示后，调整子窗口大小
        if self.child_hwnd:
            self.resize_child_window()

    def cleanup(self):
        """清理资源"""
        self.close_webview()


    def on_navigation_completed(self, args):
        pass

    def load(self, url):
        pass

    def reload(self):
        """刷新当前页面"""
        pass

    def run_js(self, script):
        pass
