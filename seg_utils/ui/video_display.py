from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import *
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
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.video_player = QVideoWidget()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.video_player)
        self.frame_grabber = VideoFrameGrabber(self)
        self.media_player.setVideoOutput([self.video_player.videoSurface(), self.frame_grabber])
        self.video_name = None  # type: str
        self.video_path = None  # type: str

        self.media_player.stateChanged.connect(self.media_state_changed.emit)
        self.media_player.positionChanged.connect(self.playback_position_changed.emit)
        self.media_player.durationChanged.connect(self.video_duration_changed.emit)
        self.media_player.error.connect(self.media_error.emit)
        self.frame_grabber.frame_available.connect(self.frame_grabbed.emit)

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
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(video_file)))
        self.video_name = os.path.splitext(os.path.basename(video_file))[0]
        self.video_path = video_file

    def grab_frame(self):
        """ trigger the capture of the next displayed frame """
        self.frame_grabber.get_frame()

    def play(self):
        """ start playing the video from the current position """
        self.media_player.play()

    def pause(self):
        """ pause the video """
        self.media_player.pause()

    def pause_and_grab(self):
        """ trigger a screen grab and pause the video """
        self.grab_frame()
        self.pause()

    def set_position(self, video_position: int):
        """
        Set the playback position of the video
        :param video_position: playback position in milliseconds
        :return: None
        """
        self.media_player.setPosition(video_position)

    def toggle_play_pause(self):
        """ toggle to play if paused or vice versa """
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.pause()
        else:
            self.play()

    def keyPressEvent(self, event: QKeyEvent):
        """ Process user key press events """
        key = event.key()
        if key == Qt.Key_Space:
            self.toggle_play_pause()
        elif key == Qt.Key_Return:
            self.pause_and_grab()


class VideoFrameGrabber(QAbstractVideoSurface):
    """ A parasitic video surface used for extracting video frames """
    frame_available = pyqtSignal(QImage, int)

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self.grab_frame = False

    def supportedPixelFormats(self, handleType):
        """ This function needs to be defined or it won't work """
        return [QVideoFrame.Format_ARGB32, QVideoFrame.Format_ARGB32_Premultiplied,
                QVideoFrame.Format_RGB32, QVideoFrame.Format_RGB24, QVideoFrame.Format_RGB565,
                QVideoFrame.Format_RGB555, QVideoFrame.Format_ARGB8565_Premultiplied,
                QVideoFrame.Format_BGRA32, QVideoFrame.Format_BGRA32_Premultiplied, QVideoFrame.Format_BGR32,
                QVideoFrame.Format_BGR24, QVideoFrame.Format_BGR565, QVideoFrame.Format_BGR555,
                QVideoFrame.Format_BGRA5658_Premultiplied, QVideoFrame.Format_AYUV444,
                QVideoFrame.Format_AYUV444_Premultiplied, QVideoFrame.Format_YUV444,
                QVideoFrame.Format_YUV420P, QVideoFrame.Format_YV12, QVideoFrame.Format_UYVY,
                QVideoFrame.Format_YUYV, QVideoFrame.Format_NV12, QVideoFrame.Format_NV21,
                QVideoFrame.Format_IMC1, QVideoFrame.Format_IMC2, QVideoFrame.Format_IMC3,
                QVideoFrame.Format_IMC4, QVideoFrame.Format_Y8, QVideoFrame.Format_Y16,
                QVideoFrame.Format_Jpeg, QVideoFrame.Format_CameraRaw, QVideoFrame.Format_AdobeDng]

    def present(self, frame: QVideoFrame):
        """ function called every new frame from the media player """
        if self.grab_frame:
            if frame.isValid():
                frame = QVideoFrame(frame)
                frame.map(QAbstractVideoBuffer.ReadOnly)
                image = QImage(frame.bits(), frame.width(), frame.height(), frame.bytesPerLine(),
                               QVideoFrame.imageFormatFromPixelFormat(frame.pixelFormat()))
                self.frame_available.emit(image, frame.startTime())
                self.grab_frame = False
        return True

    def get_frame(self):
        """ wrapper function to flag that the next frame should be grabbed. """
        self.grab_frame = True


if __name__ == '__main__':
    test_vid = r"C:\Users\Somers\Desktop\GRK008.MP4"
    app = QApplication(["test"])
    vid = VideoPlayer()
    vid.frame_grabbed.connect(lambda x, t: print(f'got frame at time {t}'))
    vid.set_video(test_vid)
    vid.show()
    vid.play()
    app.exec_()
