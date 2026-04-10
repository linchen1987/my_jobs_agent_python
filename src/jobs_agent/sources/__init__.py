import os
import logging

from jobs_agent.sources.base import BaseSource

logger = logging.getLogger(__name__)


def create_sources_from_env() -> list[BaseSource]:
    sources: list[BaseSource] = []

    eleduck_enabled = os.getenv("ELEDUCK_ENABLED", "true").lower() in (
        "true",
        "1",
        "yes",
    )
    if eleduck_enabled:
        from jobs_agent.sources.eleduck import EleduckSource

        pages = int(os.getenv("ELEDUCK_PAGES", "2"))
        offset = int(os.getenv("ELEDUCK_OFFSET", "0"))
        limit = int(os.getenv("ELEDUCK_LIMIT", "0"))
        sources.append(EleduckSource(pages=pages, offset=offset, limit=limit))
        logger.info(
            f"已启用 eleduck 数据源 (pages={pages}, offset={offset}, limit={limit})"
        )

    v2ex_enabled = os.getenv("V2EX_ENABLED", "true").lower() in (
        "true",
        "1",
        "yes",
    )
    if v2ex_enabled:
        from jobs_agent.sources.v2ex import V2exSource

        offset = int(os.getenv("V2EX_OFFSET", "0"))
        limit = int(os.getenv("V2EX_LIMIT", "0"))
        sources.append(V2exSource(offset=offset, limit=limit))
        logger.info(f"已启用 v2ex 数据源 (offset={offset}, limit={limit})")

    if not sources:
        logger.warning("没有启用任何数据源")

    return sources
