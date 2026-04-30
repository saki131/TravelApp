"""
RSS フィードパーサー
対象: JAL / ANA / Peach / Jetstar
"""
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

import feedparser
import httpx

logger = logging.getLogger(__name__)

RSS_FEEDS = {
    "jal_rss":     "https://www.jal.co.jp/info/feeds/sale.rss?r=inbound",
    "peach_rss":   "https://www.flypeach.com/ja/news/feed",
    "spring_rss":  "https://www.springjapan.com/en/feed/",
    "jetstar_rss": "https://www.jetstar.com/jp/ja/deals/feed",
}

CATEGORY_MAP = {
    "jal_rss":    "flight",
    "peach_rss":  "flight",
    "spring_rss": "flight",
    "jetstar_rss":"flight",
}


async def fetch_rss_entries(feed_key: str, url: str) -> list[dict]:
    """単一 RSS フィードを取得し、SaleEvent 用の dict リストを返す。"""
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 TravelApp RSS/1.0"})
            resp.raise_for_status()
            content = resp.text
    except Exception as e:
        logger.warning("RSS fetch failed [%s]: %s", feed_key, e)
        return []

    feed = feedparser.parse(content)
    results = []
    for entry in feed.entries:
        published_str = entry.get("published", "")
        published_dt: Optional[datetime] = None
        if published_str:
            try:
                from email.utils import parsedate_to_datetime
                published_dt = parsedate_to_datetime(published_str)
            except Exception:
                pass

        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        summary = entry.get("summary", "").strip()

        # 外部ID（重複防止）: entry.id > link のハッシュ
        raw_id = entry.get("id") or entry.get("link") or title
        external_id = hashlib.md5(raw_id.encode()).hexdigest()

        results.append({
            "category": CATEGORY_MAP.get(feed_key, "flight"),
            "title": title[:200],
            "description": summary[:2000] if summary else None,
            "sale_start": published_dt,
            "booking_url": link or None,
            "source": feed_key,
            "source_url": url,
            "is_verified": True,
            "external_id": external_id,
        })
    return results


async def collect_all_rss() -> list[dict]:
    """全 RSS フィードを収集してまとめて返す。"""
    all_entries = []
    for key, url in RSS_FEEDS.items():
        entries = await fetch_rss_entries(key, url)
        all_entries.extend(entries)
        logger.info("RSS [%s]: %d entries collected", key, len(entries))
    return all_entries
