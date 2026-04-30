"""RSSフィードと Gemini でリアルセール情報を取得してDBに保存するスクリプト"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from services.rss_parser import collect_all_rss, RSS_FEEDS, fetch_rss_entries


async def main():
    print("=== RSS フィード取得テスト ===")
    for key, url in RSS_FEEDS.items():
        entries = await fetch_rss_entries(key, url)
        t = entries[0]["title"] if entries else "(なし)"
        print(f"  {key}: {len(entries)} 件  例: {t[:60]}")

    print("\n=== 全RSS収集 ===")
    all_entries = await collect_all_rss()
    print(f"合計: {len(all_entries)} 件")

    if len(all_entries) > 0:
        print("\nDB保存中...")
        from database import SessionLocal
        from models import SaleEvent
        db = SessionLocal()
        saved = 0
        for entry in all_entries:
            source = entry.get("source")
            ext_id = entry.get("external_id")
            if not ext_id:
                continue
            exists = db.query(SaleEvent).filter(
                SaleEvent.source == source,
                SaleEvent.external_id == ext_id,
            ).first()
            if exists:
                continue
            event = SaleEvent(**{k: v for k, v in entry.items() if hasattr(SaleEvent, k)})
            db.add(event)
            saved += 1
        db.commit()
        db.close()
        print(f"  {saved} 件保存")


if __name__ == "__main__":
    asyncio.run(main())
