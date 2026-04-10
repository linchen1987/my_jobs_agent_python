import logging
from typing import Optional

from jobs_agent.core.fetch import fetch_page
from jobs_agent.sources.base import BaseSource, JobListItem, JobDetail
from jobs_agent.sources.parsers.v2ex_feed import parse_v2ex_feed, _html_to_text

logger = logging.getLogger(__name__)

FEED_URL = "https://www.v2ex.com/feed/tab/jobs.xml"


class V2exSource(BaseSource):
    def __init__(self, offset: int = 0, limit: int = 0):
        self.offset = offset
        self.limit = limit

    @property
    def name(self) -> str:
        return "v2ex"

    def fetch_list(self) -> list[JobListItem]:
        xml_text = fetch_page(FEED_URL)
        if not xml_text:
            logger.error(f"fetch_list failed: RSS feed empty")
            return []

        posts = parse_v2ex_feed(xml_text)
        logger.info(f"[{self.name}] RSS feed parsed: {len(posts)} entries")

        items: list[JobListItem] = []
        for post in posts:
            items.append(
                {
                    "id": post["id"],
                    "source": self.name,
                    "url": post["url"],
                    "title": post.get("title", ""),
                    "extra": post,
                }
            )

        if self.offset > 0 or self.limit > 0:
            end = self.offset + self.limit if self.limit > 0 else None
            items = items[self.offset : end]
            logger.info(
                f"[{self.name}] slice: offset={self.offset}, limit={self.limit or 'unlimited'}, kept {len(items)}"
            )

        return items

    def fetch_detail(self, item: JobListItem) -> Optional[JobDetail]:
        extra = item.get("extra", {})
        content_text = extra.get("content_text", "")
        content_html = extra.get("content_html", "")

        if not content_text and content_html:
            content_text = _html_to_text(content_html)

        return {
            "id": item["id"],
            "source": self.name,
            "url": item["url"],
            "title": extra.get("title", item["title"]),
            "content": content_text,
            "tags": [],
            "list_item": item,
            "extra": {
                "author": extra.get("author", ""),
                "published": extra.get("published", ""),
                "updated": extra.get("updated", ""),
                "content_html_length": len(content_html),
            },
        }
