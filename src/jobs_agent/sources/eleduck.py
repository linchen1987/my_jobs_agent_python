import logging
from typing import Optional

from jobs_agent.core.fetch import fetch_json
from jobs_agent.sources.base import BaseSource, JobListItem, JobDetail
from jobs_agent.sources.parsers.eleduck_list import parse_eleduck_list

logger = logging.getLogger(__name__)


class EleduckSource(BaseSource):
    def __init__(self, pages: int = 2, offset: int = 0, limit: int = 0):
        self.pages = pages
        self.offset = offset
        self.limit = limit

    @property
    def name(self) -> str:
        return "eleduck"

    def fetch_list(self) -> list[JobListItem]:
        items: list[JobListItem] = []
        for page in range(1, self.pages + 1):
            url = f"https://svc.eleduck.com/api/v1/posts?page={page}"
            data = fetch_json(url)
            if not data:
                logger.error(f"fetch_list failed: page={page}")
                continue
            posts = parse_eleduck_list(data)
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
        post_id = item["id"]
        api_url = f"https://svc.eleduck.com/api/v1/posts/{post_id}"
        data = fetch_json(api_url)
        if not data:
            logger.error(f"fetch_detail failed: {api_url}")
            return None

        post = data.get("post", {})
        raw_content = post.get("raw_content", "")

        tags = self._parse_tags(post.get("tags", []))

        return {
            "id": item["id"],
            "source": self.name,
            "url": item["url"],
            "title": post.get("title", item["title"]),
            "content": raw_content,
            "tags": tags,
            "list_item": item,
            "extra": {
                "views_count": post.get("views_count", 0),
                "comments_count": post.get("comments_count", 0),
                "upvotes_count": post.get("upvotes_count", 0),
                "downvotes_count": post.get("downvotes_count", 0),
                "user_nickname": post.get("user", {}).get("nickname", ""),
                "category": post.get("category", {}).get("name", ""),
                "published_at": post.get("published_at", ""),
            },
        }

    @staticmethod
    def _parse_tags(api_tags: list[dict]) -> list[dict]:
        grouped: dict[str, list[str]] = {}
        for tag in api_tags:
            group_name = tag.get("tag_group", {}).get("name", "")
            tag_name = tag.get("name", "")
            if group_name and tag_name:
                grouped.setdefault(group_name, []).append(tag_name)
        return [{"category": k, "values": v} for k, v in grouped.items()]
