"""Gemini グラウンディングで実際のセール情報を取得してDBに保存するスクリプト"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from scheduler.jobs import job_gemini_grounding


async def main():
    print("=== Gemini グラウンディングでセール情報取得 ===")
    await job_gemini_grounding()
    print("完了")

    # 結果確認
    from database import SessionLocal
    from models import SaleEvent
    db = SessionLocal()
    total = db.query(SaleEvent).count()
    items = db.query(SaleEvent).filter(SaleEvent.source.like("gemini%")).order_by(SaleEvent.created_at.desc()).limit(10).all()
    db.close()
    print(f"\nDB内 Gemini由来: {len(items)} 件 / 合計: {total} 件")
    for item in items:
        print(f"  [{item.category}] {item.title[:60]}")


if __name__ == "__main__":
    asyncio.run(main())
