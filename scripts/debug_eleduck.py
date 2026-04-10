"""快速调试抓取：给定 id 或 url 查看抓取内容

用法:
  uv run debug-fetch.py L5fbk3
  uv run debug-fetch.py https://eleduck.com/posts/L5fbk3
"""

import sys
from dotenv import load_dotenv
from sources.eleduck import EleduckSource

load_dotenv()


def main():
    if len(sys.argv) < 2:
        print("用法: uv run debug-fetch.py <id_or_url>")
        sys.exit(1)

    arg = sys.argv[1]

    if arg.startswith("http"):
        post_id = arg.rstrip("/").split("/")[-1]
    else:
        post_id = arg

    source = EleduckSource()
    item = {
        "id": post_id,
        "source": "eleduck",
        "url": f"https://eleduck.com/posts/{post_id}",
        "title": "",
        "extra": {},
    }

    detail = source.fetch_detail(item)
    if not detail:
        print(f"❌ 抓取失败: {post_id}")
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


if __name__ == "__main__":
    main()
