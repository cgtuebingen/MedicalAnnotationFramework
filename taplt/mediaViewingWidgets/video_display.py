from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtMultimedia import *
from PyQt6.QtMultimediaWidgets import *
import os


class VideoPlayer(QWidget):
    """
    A custom widget for playing a video with an embedded frame extractor
    """
    media_state_changed = pyqtSignal(int)  # QMediaPlayer.state()
    playback_position_changed = pyqtSignal(int)
    video_duration_changed = pyqtSignal(int)
    media_error = pyqtSignal(QMediaPlayer.Error)
    frame_grabbed = pyqtSignal(QImage, int)

    def __init__(self):
        super(VideoPlayer, self).__init__()
        self.media_player = QMediaPlayer(None)
        self.video_player = QVideoWidget()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.video_player)
        self.frame_grabber = QImageCapture()
        self.media_player.setVideoOutput(self.video_player.videoSink())

        self.video_name = None  # type: str
        self.video_path = None  # type: str

        self.media_player.playbackStateChanged.connect(self.media_state_changed.emit)
        self.media_player.positionChanged.connect(self.playback_position_changed.emit)
        self.media_player.durationChanged.connect(self.video_duration_changed.emit)
        self.media_player.errorOccurred.connect(self.media_error.emit)
        self.resize(700, 500)

    @property
    def duration(self):
        """ Get the length of the current video in milliseconds """
        return self.media_player.duration()

    def set_video(self, video_file: str):
        """
        Set the video to be played. This function will stop playback and reset to the beginning of the video provided.
        :param video_file: path to a video file
        :return:
        """
        self.media_player.stop()
        self.media_player.setSource(QUrl.fromLocalFile(video_file))
        self.video_name = os.path.splitext(os.path.basename(video_file))[0]
        self.video_path = video_file

    def grab_frame(self):
        """ trigger the capture of the next displayed frame """
        self.frame_grabbed.emit(self.media_player.videoOutput().videoFrame().toImage(), self.media_player.position())

    def play(self):
        """ start playing the video from the current position """
        self.media_player.play()

    def pause(self):
        """ pause the video """
        self.media_player.pause()
        pass

    def pause_and_grab(self):
        """ trigger a screen grab and pause the video """
        self.pause()
        self.grab_frame()

    def set_position(self, video_position: int):
        """
        Set the playback position of the video
        :param video_position: playback position in milliseconds
        :return: None
        """
        self.media_player.setPosition(video_position)

    def toggle_play_pause(self):
        """ toggle to play if paused or vice versa """
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.pause()
        else:
            self.play()

    def keyPressEvent(self, event: QKeyEvent):
        """ Process user key press events """
        key = event.key()
        if key == Qt.Key.Key_Space:
            self.toggle_play_pause()
        elif key == Qt.Key.Key_Return:
            self.pause_and_grab()
