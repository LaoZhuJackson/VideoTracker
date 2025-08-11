# from PyQt5.QtCore import QTimer, QUrl
# from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
#
#
# class SinglePageWebEngineView(QWebEngineView):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         # 自定义页面处理
#         self.setPage(SinglePageWebEnginePage(self))
#
#     def createWindow(self, nav_type):
#         """ 重写此方法实现所有链接在当前页打开 """
#         return self  # 始终返回自身，强制在当前页打开
#
#
# class SinglePageWebEnginePage(QWebEnginePage):
#     def acceptNavigationRequest(self, url, nav_type, isMainFrame):
#         """ 拦截所有导航请求 """
#         if nav_type == QWebEnginePage.NavigationType.NavigationTypeLinkClicked:
#             # 如果是点击链接，直接在当前页加载
#             self.view().load(url)
#             return False  # 阻止默认行为
#         return super().acceptNavigationRequest(url, nav_type, isMainFrame)
#
#
