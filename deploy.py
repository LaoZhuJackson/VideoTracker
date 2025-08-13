import os
from pathlib import Path
from shutil import copy, copytree
from distutils.sysconfig import get_python_lib

# https://blog.csdn.net/qq_25262697/article/details/129302819
# https://www.cnblogs.com/happylee666/articles/16158458.html

child_webview_path = os.path.join("app", "modules", "webview", "child_webview.py")

args = [
    "python",
    "-m",
    "nuitka",
    "--show-progress",
    "--show-memory",
    "--standalone",
    "--plugin-enable=pyqt5",
    # "--windows-uac-admin",
    # "--windows-console-mode=disable",
    # 包含子进程文件
    f"--include-data-file={child_webview_path}={child_webview_path}",
    # 添加文件
    "--include-data-dir=app/resource/images=app/resource/images",
    "--include-data-dir=asset=asset",
    '--output-dir=dist/main',
    "--windows-icon-from-ico=asset/logo.ico",
    # 额外模组
    "--include-module=app.modules.webview.child_webview",
    'main.py',
]

os.system(' '.join(args))

# copy site-packages to dist folder
dist_folder = Path("dist/main/main.dist")
site_packages = Path(get_python_lib())

copied_libs = []

# for src in copied_libs:
#     src = site_packages / src
#     dist = dist_folder / src.name
#
#     print(f"Coping site-packages `{src}` to `{dist}`")
#
#     try:
#         if src.is_file():
#             copy(src, dist)
#         else:
#             copytree(src, dist)
#     except:
#         pass


# copy standard library
copied_files = ["subprocess.py", "uuid.py", "_winapi.py"]
for file in copied_files:
    src = site_packages.parent / file
    dist = dist_folder / src.name

    print(f"Coping stand library `{src}` to `{dist}`")

    try:
        if src.is_file():
            copy(src, dist)
        else:
            copytree(src, dist)
    except Exception as e:
        print(f"copy {src} to `{dist}` error:{e}")
