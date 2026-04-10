import logging
import os
import time

from jobs_agent.sources.base import BaseSource, JobDetail

logger = logging.getLogger(__name__)

DETAIL_DELAY = float(os.getenv("FETCH_DETAIL_DELAY", "3.0"))


def fetch_and_parse_all(
    sources: list[BaseSource],
    analyzed_ids: set | None = None,
    detail_delay: float | None = None,
) -> list[JobDetail]:
    if detail_delay is None:
        detail_delay = DETAIL_DELAY

    all_details: list[JobDetail] = []

    for source in sources:
        items = source.fetch_list()
        logger.info(f"[{source.name}] list: {len(items)} items")

        if analyzed_ids:
            before = len(items)
            items = [
                it for it in items if source.global_id(it["id"]) not in analyzed_ids
            ]
            logger.info(f"[{source.name}] dedup: skipped {before - len(items)}")

        for i, item in enumerate(items, 1):
            logger.info(f"[{source.name}] [{i}/{len(items)}] {item['title']}")

            detail = source.fetch_detail(item)
            if detail:
                all_details.append(detail)

            if i < len(items) and detail_delay > 0:
                time.sleep(detail_delay)

    logger.info(f"fetch_and_parse_all done: {len(all_details)} details")
    return all_details
