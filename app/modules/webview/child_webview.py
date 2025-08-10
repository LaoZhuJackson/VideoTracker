# child_webview.py
# 运行方式: python child_webview.py "<window_title>" "<url>"

import sys
import webview


def main():
    if len(sys.argv) < 3:
        print("Usage: python child_webview.py <window_title> <url>")
        return
    title = sys.argv[1]
    url = sys.argv[2]

    # 创建窗口（在 Windows 上，pywebview 会优先使用 WebView2）
    webview.create_window(title, url, frameless=False)
    # start 必须在主线程，这里是独立进程，没问题
    webview.start(debug=False)


if __name__ == "__main__":
    main()
