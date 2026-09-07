from base_api.modules.errors import (
    VideoUnavailable,
    NotFound,
    NetworkError,
    BotDetection,
    ProxyError,
    UnknownNetworkError,
    DownloadFailed,
)


class VideoIsProcessing(Exception):
    def __init__(self):
        self.msg = "The video is still processing on spankbang's servers!"


__all__ = [
    "VideoIsProcessing",
    "VideoUnavailable",
    "NotFound",
    "NetworkError",
    "BotDetection",
    "ProxyError",
    "UnknownNetworkError",
    "DownloadFailed",
]

