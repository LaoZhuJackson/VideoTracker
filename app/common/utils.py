import platform
import ctypes
import win32gui
import win32con


def embed_window(window, container):
    """将窗口嵌入到容器中（Windows实现）"""
    if platform.system() != 'Windows':
        raise NotImplementedError("当前仅支持Windows系统")

    # 获取窗口句柄
    hwnd = window._hWnd if hasattr(window, '_hWnd') else None

    if not hwnd:
        # 使用pywebview的win32 API获取句柄
        try:
            import webview.win32
            hwnd = webview.win32.get_window_handle(window)
        except Exception as e:
            print(f"获取窗口句柄失败: {e}")
            return False

    if not hwnd:
        print("无法获取webview窗口句柄")
        return False

        # 获取容器句柄
    container_hwnd = int(container.winId())

    try:
        # 设置父窗口
        win32gui.SetParent(hwnd, container_hwnd)

        # 移除边框
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        style = style & ~win32con.WS_BORDER & ~win32con.WS_THICKFRAME
        win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)

        # 调整大小
        rect = container.contentsRect()
        win32gui.MoveWindow(hwnd, 0, 0, rect.width(), rect.height(), True)

        return True
    except Exception as e:
        print(f"窗口嵌入失败: {e}")
        return False


def get_video_control_js(action, seconds=10):
    """获取控制视频的JS代码"""
    if action == "toggle":
        return """
        var videos = document.querySelectorAll('video');
        if (videos.length > 0) {
            for (var i = 0; i < videos.length; i++) {
                if (videos[i].paused) {
                    videos[i].play();
                } else {
                    videos[i].pause();
                }
            }
        }
        """
    elif action == "forward":
        return f"""
        var videos = document.querySelectorAll('video');
        if (videos.length > 0) {{
            for (var i = 0; i < videos.length; i++) {{
                videos[i].currentTime += {seconds};
            }}
        }}
        """
    elif action == "backward":
        return f"""
        var videos = document.querySelectorAll('video');
        if (videos.length > 0) {{
            for (var i = 0; i < videos.length; i++) {{
                videos[i].currentTime -= {seconds};
            }}
        }}
        """
    return ""