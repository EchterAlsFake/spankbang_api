import re

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Referer": "https://spankbang.com",
}

cookies = {
    "age_pass": "1",
    "pg_interstitial_v5": "1",
    "pg_pop_v5": "1",
    "player_quality": "1080",
    "preroll_skip": "1",
    "backend_version": "main",
    "videos_layout": "four-col"
}

PATTERN_RESOLUTION = re.compile(r'(\d+p)\.mp4')

REGEX_VIDEO_RATING = re.compile(r'<span class="rate">(.*?)</span>')
REGEX_VIDEO_AUTHOR = re.compile(r'<span class="name">(.*?)</span>')
REGEX_VIDEO_LENGTH = re.compile(r'<span class="i-length">(.*?)</span>')
