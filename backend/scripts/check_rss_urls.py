"""RSS URLの疎通テスト"""
import asyncio
import httpx

URLS = [
    ("JAL_sale", "https://www.jal.co.jp/info/feeds/sale.rss"),
    ("JAL_news",  "https://www.jal.co.jp/info/feeds/news.rss"),
    ("peach_ja",  "https://www.flypeach.com/ja/news/feed"),
    ("spring_ja", "https://www.springjapan.com/ja/feed/"),
    ("spring_en", "https://www.springjapan.com/en/feed/"),
    ("jetstar_rss", "https://www.jetstar.com/jp/ja/rss"),
    ("jetstar_news", "https://www.jetstar.com/shared/en/rss/news.rss"),
]


async def check(name, url):
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as c:
            r = await c.get(url, headers={"User-Agent": "Mozilla/5.0"})
            ct = r.headers.get("content-type", "")
            body = r.text[:100]
            print(f"{name}: {r.status_code}  ct={ct[:40]}  body={body[:60]}")
    except Exception as e:
        print(f"{name}: ERROR {e}")


async def main():
    await asyncio.gather(*[check(n, u) for n, u in URLS])


if __name__ == "__main__":
    asyncio.run(main())
