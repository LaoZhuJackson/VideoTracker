# child_webview.py
# 运行方式: python child_webview.py "<window_title>" "<url>"
import ctypes
import json
import os
import sys
import threading
import traceback

import webview
from webview import Window


class WebViewManager:
    def __init__(self, window: Window):
        self.window = window
        self.history = []
        # 初始设 -1，表示没有历史
        self.current_index = -1
        self.js_results = {}

        # 绑定事件（注意：事件可能不传 url 参数）
        window.events.loaded += self.on_navigation_completed
        window.events.shown += self.on_window_shown

    def on_navigation_completed(self, *args):
        """导航完成事件处理 - 兼容不同事件签名"""
        try:
            # 尝试从事件参数中提取 url（有的后端会传 window 或 url 字符串）
            url = None
            if args:
                first = args[0]
                # 如果直接是字符串
                if isinstance(first, str):
                    url = first
                else:
                    # 可能传的是 window 对象或类似结构，尝试取属性
                    url = getattr(first, "url", None) or getattr(first, "href", None) or getattr(first, "location", None)

            # 最后尝试从 self.window 取当前 url（某些后端支持）
            if not url:
                try:
                    url = self.window.get_current_url()
                except Exception:
                    url = getattr(self.window, "url", None) or ""

            # 正常化为字符串
            url = url or ""
            print(f"Navigation completed: {url}", flush=True)

            # 添加到历史记录（安全地处理 current_index）
            if not self.history or (self.current_index < 0) or (self.history[self.current_index] != url):
                # 清除当前索引之后的历史记录（如果有）
                if len(self.history) - 1 > self.current_index >= 0:
                    self.history = self.history[:self.current_index + 1]

                self.history.append(url)
                self.current_index = len(self.history) - 1

            # 输出历史状态
            self.output_history_state()
        except Exception:
            print("NAV_ON_COMPLETED_ERROR:" + traceback.format_exc(), flush=True)

        # 添加 JS 注入
        inject_js = """
        document.addEventListener('click', function(e) {
            let target = e.target;
            while (target && target.tagName !== 'A') {
                target = target.parentElement;
            }
            if (target && target.tagName === 'A' && target.href) {
                e.preventDefault();
                window.pywebview.api.link_clicked(target.href);
            }
        }, true);
        """
        try:
            self.window.evaluate_js(inject_js)
        except Exception as e:
            print(f"INJECT_JS_ERROR: {e}", flush=True)

    def output_history_state(self):
        """输出历史状态到stdout（安全）"""
        try:
            current_url = ""
            if self.history and 0 <= self.current_index < len(self.history):
                current_url = self.history[self.current_index]
            state = {
                "can_go_back": self.can_go_back(),
                "can_go_forward": self.can_go_forward(),
                "current_url": current_url
            }
            print(f"HISTORY_STATE:{json.dumps(state)}", flush=True)
        except Exception:
            print("HISTORY_STATE_ERROR:" + traceback.format_exc(), flush=True)

    def on_window_shown(self):
        """窗口显示事件处理"""
        print("Window shown", flush=True)

    def can_go_back(self):
        """是否可以后退"""
        return self.current_index > 0

    def can_go_forward(self):
        """是否可以前进"""
        return self.current_index < len(self.history) - 1

    def go_back(self):
        """后退"""
        try:
            if self.can_go_back():
                self.current_index -= 1
                url = self.history[self.current_index]
                print(f"GO_BACK -> loading {url}", flush=True)
                self.window.load_url(url)
                self.output_history_state()
        except Exception:
            print("GO_BACK_ERROR:" + traceback.format_exc(), flush=True)

    def go_forward(self):
        """前进"""
        try:
            if self.can_go_forward():
                self.current_index += 1
                url = self.history[self.current_index]
                print(f"GO_FORWARD -> loading {url}", flush=True)
                self.window.load_url(url)
                self.output_history_state()
        except Exception:
            print("GO_FORWARD_ERROR:" + traceback.format_exc(), flush=True)

    def reload(self):
        """刷新页面"""
        try:
            print(f"Reloading:{self.history[self.current_index]}", flush=True)
            self.window.evaluate_js("location.reload(true);")
        except Exception:
            print("RELOAD_ERROR:" + traceback.format_exc(), flush=True)

    def run_js(self, script, callback_id):
        """执行JavaScript（可扩展）"""
        try:
            # 如果底层支持 evaluate_js，可以在这里调用并回调 handle_js_result
            # self.window.evaluate_js(script, lambda result: self.handle_js_result(result, callback_id))
            print(f"RUN_JS_REQUEST:{callback_id}:{script}", flush=True)
        except Exception as e:
            print(f"JS_ERROR:{callback_id}:{str(e)}", flush=True)

    def handle_js_result(self, result, callback_id):
        """处理JavaScript执行结果"""
        try:
            print(f"JS_RESULT:{callback_id}:{json.dumps(result)}", flush=True)
        except Exception:
            print(f"JS_RESULT:{callback_id}:<non-json-result>", flush=True)


def read_commands(manager):
    while True:
        try:
            raw = sys.stdin.readline()
            if raw == '':
                print("STDIN_EOF", flush=True)
                break
            line = raw.strip()
            print(f"CMD_RECEIVED:{line}", flush=True)

            if not line:
                continue

            if line in ("reload", "refresh"):
                manager.reload()
            elif line in ("back", "go_back"):
                manager.go_back()
            elif line in ("forward", "go_forward"):
                manager.go_forward()
            elif line.startswith("load:"):
                try:
                    url = line.split(":", 1)[1]
                    manager.window.load_url(url)
                except Exception:
                    print("LOAD_ERROR:" + traceback.format_exc(), flush=True)
            elif line == "get_history_state":
                manager.output_history_state()
            elif line.startswith("run_js:"):
                try:
                    parts = line.split(":", 2)
                    if len(parts) == 3:
                        callback_id = parts[1]
                        js_script = parts[2]
                        manager.run_js(js_script, callback_id)
                except Exception:
                    print("RUN_JS_PARSE_ERROR:" + traceback.format_exc(), flush=True)
            elif line == "destroy":
                manager.window.destroy()
            else:
                print(f"UNKNOWN_CMD:{line}", flush=True)

        except Exception:
            print("COMMAND_ERROR:" + traceback.format_exc(), flush=True)

class ApiBridge:
    def __init__(self, manager):
        self.manager = manager

    def link_clicked(self, url):
        print(f"LINK_CLICKED:{url}", flush=True)
        # 直接覆盖当前页面
        self.manager.window.load_url(url)


def main():
    if len(sys.argv) < 3:
        print("Usage: python child_webview.py <window_title> <url>")
        return
    title = sys.argv[1]
    url = sys.argv[2]

    # 创建窗口（在 Windows 上，pywebview 会优先使用 WebView2）
    window = webview.create_window(title, url, frameless=False)
    manager = WebViewManager(window)

    api = ApiBridge(manager)
    window.expose(api.link_clicked)

    # 启动命令读取线程
    t = threading.Thread(target=read_commands, args=(manager,), daemon=True)
    t.start()

    # start 必须在主线程
    webview.start(debug=False)


if __name__ == "__main__":
    main()
