# child_webview.py
# 运行方式: python child_webview.py "<window_title>" "<url>"
import json
import sys
import threading

import webview
from webview import Window


class WebViewManager:
    def __init__(self, window: Window):
        self.window = window
        self.history = []
        self.current_index = 0
        self.js_results = {}

        # 绑定事件
        window.events.loaded += self.on_navigation_completed
        window.events.shown += self.on_window_shown

    def on_navigation_completed(self, url):
        """导航完成事件处理"""
        print(f"Navigation completed: {url}")
        # 添加到历史记录
        if not self.history or self.history[self.current_index] != url:
            # 清除当前索引之后的历史记录（如果有）
            if self.current_index < len(self.history) - 1:
                self.history = self.history[:self.current_index + 1]

            self.history.append(url)
            self.current_index = len(self.history) - 1
        # 输出历史状态
        self.output_history_state()

    def output_history_state(self):
        """输出历史状态到stdout"""
        state = {
            "can_go_back": self.can_go_back(),
            "can_go_forward": self.can_go_forward(),
            "current_url": self.history[self.current_index] if self.current_index >= 0 else ""
        }
        print(f"HISTORY_STATE:{json.dumps(state)}", flush=True)

    def on_window_shown(self):
        """窗口显示事件处理"""
        print("Window shown")

    def can_go_back(self):
        """是否可以后退"""
        return self.current_index > 0

    def can_go_forward(self):
        """是否可以前进"""
        return self.current_index < len(self.history) - 1

    def go_back(self):
        """后退"""
        if self.can_go_back():
            self.current_index -= 1
            self.window.load_url(self.history[self.current_index])
            self.output_history_state()

    def go_forward(self):
        """前进"""
        if self.can_go_forward():
            self.current_index += 1
            self.window.load_url(self.history[self.current_index])
            self.output_history_state()

    def reload(self):
        """刷新页面"""
        if self.current_index >= 0:
            print("Reloading")
            self.window.load_url(self.history[self.current_index])

    def run_js(self, script, callback_id):
        """执行JavaScript"""
        try:
            # self.window.evaluate_js(script, lambda result: self.handle_js_result(result, callback_id))
            pass
        except Exception as e:
            print(f"JS_ERROR:{callback_id}:{str(e)}", flush=True)

    def handle_js_result(self, result, callback_id):
        """处理JavaScript执行结果"""
        print(f"JS_RESULT:{callback_id}:{json.dumps(result)}", flush=True)


def read_commands(manager):
    while True:
        try:
            line = sys.stdin.readline().strip()
            if not line:
                break

            if line == "reload":
                manager.reload()
            elif line == "back":
                manager.go_back()
            elif line == "forward":
                manager.go_forward()
            elif line.startswith("run_js:"):
                parts = line.split(":", 2)
                if len(parts) == 3:
                    callback_id = parts[1]
                    js_script = parts[2]
                    manager.run_js(js_script, callback_id)
        except Exception as e:
            print(f"COMMAND_ERROR:{str(e)}", flush=True)


def main():
    if len(sys.argv) < 3:
        print("Usage: python child_webview.py <window_title> <url>")
        return
    title = sys.argv[1]
    url = sys.argv[2]

    # 创建窗口（在 Windows 上，pywebview 会优先使用 WebView2）
    window = webview.create_window(title, url, frameless=False)
    manager = WebViewManager(window)

    # 启动命令读取线程
    t = threading.Thread(target=read_commands, args=(manager,), daemon=True)
    t.start()

    # start 必须在主线程，这里是独立进程，没问题
    webview.start(debug=False)


if __name__ == "__main__":
    main()
