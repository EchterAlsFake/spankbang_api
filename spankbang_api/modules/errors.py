from base_api.modules.errors import (
    ScraperException,
    VideoUnavailable,
    NotFound,
    NetworkError,
    BotDetection,
    ProxyError,
    UnknownNetworkError,
    DownloadFailed,
)


class VideoIsProcessing(ScraperException):
    def __init__(self, msg: str = "The video is still processing on spankbang's servers!"):
        super().__init__(msg)


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
