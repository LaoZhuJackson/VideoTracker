import json
import sys
import subprocess
import ctypes
import uuid
from ctypes import wintypes
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import QTimer, Qt, QRect, pyqtSignal, QEvent

from app.common.utils import translate_to_specific_window, set_focus_state

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
WS_EX_NOACTIVATE = 0x08000000

WS_EX_APPWINDOW = 0x00040000
GWL_EXSTYLE = -20

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
    # 添加信号
    navigation_completed = pyqtSignal(str)
    history_state_changed = pyqtSignal(bool, bool)
    js_result_received = pyqtSignal(str, object)
    # 添加新信号
    webview_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.parent = parent
        self.child_proc = None
        self.parent_hwnd = None
        self.child_hwnd = None
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(100)
        self._poll_timer.timeout.connect(self._poll_embed)

        # 用于存储JS回调
        self.js_callbacks = {}

        # 启动历史状态读取定时器
        self.history_timer = QTimer(self)
        self.history_timer.setInterval(500)
        self.history_timer.timeout.connect(self.check_history_state)

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

        cmd = [sys.executable, CHILD_PY, title, url]
        # 添加启动信息参数，告诉子进程不要激活窗口
        startupinfo = subprocess.STARTUPINFO()
        # 使用stdin/stdout管道进行通信
        self.child_proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',  # 强制用 UTF-8 解码
            errors='replace',  # 遇到非法字节替换
            bufsize=1,  # 行缓冲
            universal_newlines=True,
        )
        print(f"PARENT: started child pid={self.child_proc.pid}", flush=True)
        # 启动stdout读取线程
        self.start_stdout_reader()

        self._poll_timer.start()

    def start_stdout_reader(self):
        """启动stdout读取线程"""
        from threading import Thread
        self.reader_thread = Thread(target=self.read_stdout, daemon=True)
        self.reader_thread.start()

    def read_stdout(self):
        """线程中循环读取子进程的stdout输出，实现父进程响应子进程"""
        while self.child_proc and self.child_proc.poll() is None:
            try:
                raw = self.child_proc.stdout.readline()
                if raw is None:
                    continue
                line = raw.strip()
                if not line:
                    continue

                # debug: 打印所有原始输出
                print(f"PARENT: CHILD_STDOUT_RAW: {repr(line)}", flush=True)

                # 添加点击消息处理
                if line == "WEBVIEW_CLICKED":
                    self.webview_clicked.emit()

                # 处理历史状态更新
                if line.startswith("HISTORY_STATE:"):
                    try:
                        state_json = line[len("HISTORY_STATE:"):]
                        state = json.loads(state_json)
                        self.history_state_changed.emit(
                            state.get("can_go_back", False),
                            state.get("can_go_forward", False)
                        )
                    except Exception as e:
                        print(f"PARENT: Error parsing history state: {e}", flush=True)

                elif line.startswith("JS_RESULT:"):
                    parts = line.split(":", 2)
                    if len(parts) == 3:
                        callback_id = parts[1]
                        result_str = parts[2]
                        try:
                            result = json.loads(result_str)
                            self.js_result_received.emit(callback_id, result)
                        except:
                            self.js_result_received.emit(callback_id, result_str)

                elif line.startswith("JS_ERROR:"):
                    parts = line.split(":", 2)
                    if len(parts) == 3:
                        callback_id = parts[1]
                        error = parts[2]
                        self.js_result_received.emit(callback_id, Exception(error))

                elif line.startswith("Navigation completed:"):
                    url = line[len("Navigation completed:"):].strip()
                    self.navigation_completed.emit(url)

                # 其他调试输出（例如 CMD_RECEIVED 会从子进程 echo 回来）
                # 这里已被打印为 CHILD_STDOUT_RAW

            except Exception as e:
                print(f"PARENT: Error reading stdout: {e}", flush=True)
                break

    def close_webview(self):
        """关闭WebView"""
        if self.child_proc and self.child_proc.poll() is None:
            self.send_command("destroy")
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
        self.parent_hwnd = host_hwnd
        # 将焦点转移到父窗口句柄
        translate_to_specific_window(child_hwnd, host_hwnd)

        self.embed_area.installEventFilter(self)
        set_focus_state(child_hwnd, False)
        # 调整初始大小
        self.resize_child_window()

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
        if source is self.embed_area:
            if event.type() == QEvent.Resize:
                self.resize_child_window()
            # 添加焦点处理
            # elif source is self.embed_area and event.type() == QEvent.FocusIn:
            #     set_focus_state(self.parent_hwnd, False)
            # elif event.type() == QEvent.FocusOut:
            #     set_focus_state(self.child_hwnd, False)
        return super().eventFilter(source, event)

    def showEvent(self, event):
        super().showEvent(event)
        # 在控件首次显示后，调整子窗口大小
        if self.child_hwnd:
            self.resize_child_window()

    def cleanup(self):
        """清理资源"""
        self.close_webview()

    def send_command(self, command):
        """向子进程发送命令"""
        if not self.child_proc:
            print("PARENT: send_command called but child_proc is None", flush=True)
            return

        if self.child_proc.poll() is not None:
            print(f"PARENT: child process already exited (rc={self.child_proc.poll()})", flush=True)
            return

        if not self.child_proc.stdin:
            print("PARENT: child_proc.stdin is None", flush=True)
            return

        try:
            print(f"PARENT: SENDING_CMD:{command}", flush=True)
            self.child_proc.stdin.write(command + "\n")
            self.child_proc.stdin.flush()
        except Exception as e:
            print(f"PARENT: Error sending command: {e}", flush=True)

    def on_navigation_completed(self, args):
        pass

    def go_back(self):
        """后退"""
        self.send_command("back")

    def go_forward(self):
        """前进"""
        self.send_command("forward")

    def reload(self):
        """刷新页面"""
        print("Reloading...")
        self.send_command("reload")

    def load(self, url):
        """加载指定URL"""
        self.send_command(f"load:{url}")

    def run_js(self, script):
        """执行JavaScript代码"""
        callback_id = str(uuid.uuid4())
        self.send_command(f"run_js:{callback_id}:{script}")
        return callback_id

    def check_history_state(self):
        """检查历史状态（定时调用）"""
        if self.child_proc and self.child_proc.poll() is None:
            # 请求历史状态更新
            self.send_command("get_history_state")
