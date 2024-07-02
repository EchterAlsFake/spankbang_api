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
        self.html_content = Core().get_content(url, headers=headers, cookies=cookies)
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
    def title(self):
        return self.json_tags.get("name")

    @cached_property
    def description(self):
        return self.json_tags.get("description")

    @cached_property
    def thumbnail(self):
        return self.json_tags.get("thumbnailUrl")

    @cached_property
    def publish_date(self):
        return self.json_tags.get("uploadDate")

    @cached_property
    def embed_url(self):
        return self.json_tags.get("embedUrl")

    @cached_property
    def keywords(self):
        return self.json_tags.get("keywords")

    @cached_property
    def m3u8_master(self):
        return self.urls_list[0]

    def get_segments(self, quality):
        quality = Core().fix_quality(quality)
        segments = Core().get_segments(quality, base_qualities=base_qualities, m3u8_base_url=self.m3u8_master,
                                   seperator="-", source="spankbang")

        fixed_segments = []

        for seg in segments:
            fixed_segments.append(str(seg).split(".mp4.urlset/")[1])

        return fixed_segments

    def download(self, path, quality, downloader="threaded", callback=Callback.text_progress_bar, no_title=False, use_hls=True):
        if no_title is False:
            path = Path(path + Core().strip_title(self.title) + ".mp4")

        if use_hls:
            Core().download(video=self, quality=quality, path=path, callback=callback, downloader=downloader)


class Client():
    def get_video(self, url):
        return Video(url)

