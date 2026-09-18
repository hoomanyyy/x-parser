import html
import logging
import os
import re
import time
from urllib.parse import quote

import feedparser
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = (os.getenv("BASE_URL") or "").rstrip("/")
REQUEST_TIMEOUT = 20
SEEN_LIMIT = 200

STATUS_RE = re.compile(r"/status(?:es)?/(\d+)")
BREAK_RE = re.compile(r"<\s*br\s*/?\s*>|</\s*(?:p|div|blockquote|li|h[1-6])\s*>", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")
SPACES_RE = re.compile(r"[ \t\xa0]+")
BLANK_LINES_RE = re.compile(r"\n{3,}")

logger = logging.getLogger(__name__)


def extract_post_id(value):
    if value is None:
        return None
    text = str(value).strip()
    if text.isdigit():
        return int(text)
    match = STATUS_RE.search(text)
    return int(match.group(1)) if match else None


def clean_text(value):
    if not value:
        return ""
    text = BREAK_RE.sub("\n", value)
    text = TAG_RE.sub("", text)
    text = html.unescape(text)
    lines = [SPACES_RE.sub(" ", line).strip() for line in text.splitlines()]
    return BLANK_LINES_RE.sub("\n\n", "\n".join(lines)).strip()


def find_new_posts(posts, seen):
    seen_set = set(seen)
    known_positions = [index for index, post in enumerate(posts) if post["key"] in seen_set]
    boundary = known_positions[-1] if known_positions else -1
    seen_numbers = [int(key) for key in seen if key.isdigit()]
    newest_seen = max(seen_numbers) if seen_numbers else None

    new_posts = []
    for index, post in enumerate(posts):
        if post["key"] in seen_set:
            continue
        above_known = index < boundary
        newer = newest_seen is not None and post["post_id"] is not None and post["post_id"] > newest_seen
        if above_known or newer:
            new_posts.append(post)

    new_posts.reverse()
    return new_posts


def merge_seen(posts, seen, exclude=()):
    exclude = set(exclude)
    merged = []
    added = set()
    for key in [post["key"] for post in posts] + list(seen):
        if key in exclude or key in added:
            continue
        added.add(key)
        merged.append(key)
    return merged[:SEEN_LIMIT]


def newest_id(keys):
    numbers = [int(key) for key in keys if key.isdigit()]
    return str(max(numbers)) if numbers else None


class GetPosts:

    def __init__(self, username):
        self.username = username

    def build_url(self):
        return f"{BASE_URL}/twitter/user/{quote(self.username)}/forceWebApi=1&_={int(time.time())}"

    def posts(self):
        if not BASE_URL:
            logger.error("BASE_URL is not set in .env")
            return None

        url = self.build_url()

        try:
            response = requests.get(
                url,
                timeout=REQUEST_TIMEOUT,
                headers={
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                    "User-Agent": "Mozilla/5.0",
                },
            )
        except requests.RequestException as e:
            logger.warning("Request failed for @%s: %s", self.username, e)
            return None

        if response.status_code != 200:
            logger.warning("RSS error for @%s: HTTP %s", self.username, response.status_code)
            return None

        feed = feedparser.parse(response.content)

        if feed.bozo and not feed.entries:
            logger.warning("Invalid feed for @%s: %s", self.username, feed.get("bozo_exception"))
            return None

        posts = []
        keys = set()

        for entry in feed.entries:
            link = entry.get("link") or ""
            guid = entry.get("id") or link
            post_id = extract_post_id(link) or extract_post_id(guid)
            key = str(post_id) if post_id is not None else guid

            if not key or key in keys:
                continue

            keys.add(key)
            posts.append({
                "key": key,
                "post_id": post_id,
                "title": entry.get("title") or "",
                "description": entry.get("description") or "",
                "text": clean_text(entry.get("description")) or clean_text(entry.get("title")),
                "link": link,
                "pubDate": entry.get("published"),
                "author": entry.get("author"),
            })

        logger.debug("Fetched %s posts for @%s", len(posts), self.username)
        return posts