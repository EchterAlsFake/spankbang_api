import re
import json
import html
import logging

from base_api.base import Core, setup_api
from base_api.modules.download import legacy_download, threaded, default, FFMPEG
from base_api.modules.progress_bars import Callback
from base_api.modules.quality import Quality
from modules.consts import *
from bs4 import BeautifulSoup
from functools import cached_property
from pathlib import Path

setup_api(True)
base_qualities = ["240p", "320p", "480p", "720p", "1080p", "4k"]


class Video():
    def __init__(self, url):
        self.html_content = Core().get_content(url, headers=headers, cookies=cookies).decode("utf-8")
        self.soup = BeautifulSoup(self.html_content, "lxml")
        self.extract_script_2()
        self.extract_script_1()

    def extract_script_1(self):
        """This extracts the script with the basic video information"""
        main_container = self.soup.find("main", class_="main-container")
        script_tag = main_container.find('script', {"type": "application/ld+json"})
        self.json_tags = json.loads(html.unescape(script_tag.string))

    def extract_script_2(self):
        """This extracts the script with the m3u8 URLs which contain the segments used for downloading"""
        main_container = self.soup.find('main', class_='main-container')
        script_tag = main_container.find('script', {'type': 'text/javascript'})
        stream_data_js = re.search(r'var stream_data = ({.*?});', script_tag.text, re.DOTALL).group(1)
        m3u8_pattern = re.compile(r"'m3u8': \['(https://[^']+master.m3u8[^']*)'\]")
        resolution_pattern = re.compile(r"'(240p|320p|480p|720p|1080p|4k)': \['(https://[^']+.mp4[^']*)'\]")

        # Extract m3u8 master URL
        m3u8_match = m3u8_pattern.search(stream_data_js)
        m3u8_url = m3u8_match.group(1) if m3u8_match else None

        # Extract resolution URLs
        resolution_matches = resolution_pattern.findall(stream_data_js)
        resolution_urls = [url for res, url in resolution_matches]

        # Combine the URLs with m3u8 first
        self.urls_list = [m3u8_url] + resolution_urls if m3u8_url else resolution_urls
        # (Damn I love ChatGPT xD)

    @cached_property
    def title(self) -> str:
        """Returns the title of the video"""
        return self.json_tags.get("name")

    @cached_property
    def description(self) -> str:
        """Returns the description of the video"""
        return self.json_tags.get("description")

    @cached_property
    def thumbnail(self) -> str:
        """Returns the thumbnail of the video"""
        return self.json_tags.get("thumbnailUrl")

    @cached_property
    def publish_date(self) -> str:
        """Returns the publish date of the video"""
        return self.json_tags.get("uploadDate")

    @cached_property
    def embed_url(self):
        """Returns the url of the video embed"""
        return self.json_tags.get("embedUrl")

    @cached_property
    def tags(self) -> list:
        """Returns the keywords of the video"""
        return self.json_tags.get("keywords")

    @cached_property
    def author(self) -> str:
        """Returns the author of the video"""
        return REGEX_VIDEO_AUTHOR.search(self.html_content).group(1)

    @cached_property
    def rating(self) -> str:
        """Returns the rating of the video"""
        return REGEX_VIDEO_RATING.search(self.html_content).group(1)

    @cached_property
    def length(self) -> str:
        """Returns the length in possibly 00:00 format"""
        return REGEX_VIDEO_LENGTH.search(self.html_content).group(1)

    @cached_property
    def m3u8_master(self) -> str:
        """Returns the master m3u8 URL of the video"""
        return self.urls_list[0]

    @cached_property
    def direct_download_urls(self) -> list:
        """returns the CDN URLs of the video (direct download links)"""
        _ = []
        for idx, url in enumerate(self.urls_list):
            if idx != 0:
                _.append(url)
        return _

    @cached_property
    def video_qualities(self) -> list:
        """Returns the available qualities of the video"""
        quals = self.direct_download_urls
        qualities = set()
        for url in quals:
            match = PATTERN_RESOLUTION.search(url)
            if match:
                qualities.add(match.group(1).strip("p"))
        return sorted(qualities, key=int)

    def get_segments(self, quality) -> list:
        """Returns a list of segments by a given quality for HLS streaming"""
        quality = Core().fix_quality(quality)
        segments = Core().get_segments(quality, base_qualities=base_qualities, m3u8_base_url=self.m3u8_master,
                                   seperator="-", source="spankbang")

        fixed_segments = []

        for seg in segments:
            fixed_segments.append(str(seg).split(".mp4.urlset/")[1])

        return fixed_segments

    def download(self, path, quality, downloader="threaded", callback=Callback.text_progress_bar, no_title=False, use_hls=True):
        quality = Core().fix_quality(quality)
        if no_title is False:
            path = Path(path + Core().strip_title(self.title) + ".mp4")

        if use_hls:
            Core().download(video=self, quality=quality, path=path, callback=callback, downloader=downloader)

        else:
            cdn_urls = self.direct_download_urls
            quals = self.video_qualities
            quality_url_map = {qual: url for qual, url in zip(quals, cdn_urls)}

            quality_map = {
                Quality.BEST: max(quals, key=lambda x: int(x)),
                Quality.HALF: sorted(quals, key=lambda x: int(x))[len(quals) // 2],
                Quality.WORST: min(quals, key=lambda x: int(x))
            }

            selected_quality = quality_map[quality]
            download_url = quality_url_map[selected_quality]
            legacy_download(stream=True, url=download_url, path=path, callback=callback)


class Client:

    @classmethod
    def get_video(cls, url) -> Video:
        return Video(url)
