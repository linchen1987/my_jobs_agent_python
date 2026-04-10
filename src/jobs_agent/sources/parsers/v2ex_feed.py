import re
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

ATOM_NS = "http://www.w3.org/2005/Atom"

_TOPIC_ID_RE = re.compile(r"/t/(\d+)")


def _extract_topic_id(entry: ET.Element) -> str:
    for link in entry.findall(f"{{{ATOM_NS}}}link"):
        href = link.get("href", "")
        m = _TOPIC_ID_RE.search(href)
        if m:
            return m.group(1)

    entry_id = entry.findtext(f"{{{ATOM_NS}}}id", "")
    m = _TOPIC_ID_RE.search(entry_id)
    if m:
        return m.group(1)

    return ""


def _strip_ns(tag: str) -> str:
    if tag.startswith(f"{{{ATOM_NS}}}"):
        return tag[len(ATOM_NS) + 2 :]
    return tag


def _text(entry: ET.Element, child: str) -> str:
    return entry.findtext(f"{{{ATOM_NS}}}{child}", "").strip()


def _html_to_text(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n", strip=True)


def parse_v2ex_feed(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    results: list[dict] = []

    for entry in root.findall(f"{{{ATOM_NS}}}entry"):
        topic_id = _extract_topic_id(entry)
        if not topic_id:
            continue

        link_el = entry.find(f"{{{ATOM_NS}}}link[@rel='alternate']")
        url = link_el.get("href", "") if link_el is not None else ""

        content_html = _text(entry, "content")
        content_text = _html_to_text(content_html)

        author_el = entry.find(f"{{{ATOM_NS}}}author")
        author = ""
        if author_el is not None:
            author = author_el.findtext(f"{{{ATOM_NS}}}name", "").strip()

        results.append(
            {
                "id": topic_id,
                "url": url,
                "title": _text(entry, "title"),
                "content_html": content_html,
                "content_text": content_text,
                "author": author,
                "published": _text(entry, "published"),
                "updated": _text(entry, "updated"),
            }
        )

    return results
