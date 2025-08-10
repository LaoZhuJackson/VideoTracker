from PyQt5.QtCore import pyqtSlot, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaResource
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import QFrame

from app.common.signal_bus import signalBus
from app.ui.VideoWindow import Ui_video_window
from qfluentwidgets import FluentIcon as FIF, PrimaryToolButton


class VideoWindow(QFrame, Ui_video_window):
    def __init__(self, text, parent=None):
        super().__init__()
        self.setupUi(self)
        self.setObjectName(text.replace(' ', '-'))
        self.parent = parent

        self._initWidget()
        self._connect_to_slot()

    def _initWidget(self):
        # 视频播放器
        self.video_widget = QVideoWidget()
        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.video_widget)
        # 创建媒体资源并设置请求头
        resource = QMediaResource(QUrl("https://vd3.bdstatic.com/mda-ndc4d1nxgy14nztd/cae_h264_delogo/1649819428555205822/mda-ndc4d1nxgy14nztd.mp4"))
        content = QMediaContent(resource)
        self.player.setMedia(content)
        self.player.play()
        # 播放按钮
        self.PrimaryToolButton_play = PrimaryToolButton(self)
        self.PrimaryToolButton_play.setObjectName("PrimaryToolButton_play")
        self.PrimaryToolButton_play.setIcon(FIF.PLAY)
        self.gridLayout.addWidget(self.PrimaryToolButton_play, 1, 1, 1, 1)

        self.gridLayout.addWidget(self.video_widget, 0, 0, 1, 3)

    def _connect_to_slot(self):
        signalBus.getVideoUrl.connect(self.play_video)

    def play_video(self, url):
        if url:
            self.player.setMedia(QMediaContent(QUrl(url)))
            self.player.play()
        else:
            print("没有可播放的视频 URL")
