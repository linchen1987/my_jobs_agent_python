"""调试 V2EX 数据抓取

用法:
  uv run scripts/debug_v2ex.py              # 抓取 RSS feed，打印列表摘要
  uv run scripts/debug_v2ex.py 1204629      # 打印指定帖子的完整内容
  uv run scripts/debug_v2ex.py https://www.v2ex.com/t/1204629
"""

import sys
from dotenv import load_dotenv
from jobs_agent.sources.v2ex import V2exSource

load_dotenv()


def show_list(source: V2exSource):
    items = source.fetch_list()
    if not items:
        print("未获取到帖子")
        return

    print(f"共 {len(items)} 条帖子:\n")
    print(f"{'#':<4} {'ID':<10} {'Title':<60} {'Author':<20} {'Published'}")
    print("-" * 120)
    for i, item in enumerate(items, 1):
        extra = item.get("extra", {})
        print(
            f"{i:<4} {item['id']:<10} {item['title'][:58]:<60} "
            f"{extra.get('author', ''):<20} {extra.get('published', '')[:19]}"
        )


def show_detail(source: V2exSource, topic_id: str):
    item = {
        "id": topic_id,
        "source": "v2ex",
        "url": f"https://www.v2ex.com/t/{topic_id}",
        "title": "",
        "extra": {},
    }

    detail = source.fetch_detail(item)
    if not detail:
        print(f"抓取失败: {topic_id}")
        sys.exit(1)

    print(f"ID:      {detail['id']}")
    print(f"Title:   {detail['title']}")
    print(f"URL:     {detail['url']}")
    print(f"Content: ({len(detail['content'])} chars)")
    print("-" * 60)
    print(detail["content"])
    print("-" * 60)
    print(f"Tags:    {detail['tags']}")
    print(f"Extra:   {detail['extra']}")


def show_detail_from_feed(source: V2exSource, topic_id: str):
    items = source.fetch_list()
    matched = [it for it in items if it["id"] == topic_id]
    if not matched:
        print(f"RSS feed 中未找到帖子 {topic_id}，尝试直接抓取...")
        show_detail(source, topic_id)
        return

    item = matched[0]
    detail = source.fetch_detail(item)
    if not detail:
        print(f"解析失败: {topic_id}")
        sys.exit(1)

    print(f"ID:      {detail['id']}")
    print(f"Title:   {detail['title']}")
    print(f"URL:     {detail['url']}")
    print(f"Content: ({len(detail['content'])} chars)")
    print("-" * 60)
    print(detail["content"])
    print("-" * 60)
    print(f"Tags:    {detail['tags']}")
    print(f"Extra:   {detail['extra']}")


def main():
    source = V2exSource()

    if len(sys.argv) < 2:
        show_list(source)
        return

    arg = sys.argv[1]
    if arg.startswith("http"):
        topic_id = arg.rstrip("/").split("/t/")[-1].split("#")[0]
    else:
        topic_id = arg.strip()

    show_detail_from_feed(source, topic_id)


if __name__ == "__main__":
    main()
