"""
セール情報サンプルデータのシードスクリプト
"""
import sys
import os
import uuid
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from config import settings

# 今日を基準にした日付
NOW = datetime.now(timezone.utc)
TODAY = NOW.date()

SAMPLE_SALES = [
    {
        "category": "flight",
        "title": "スプリング・ジャパン タイムセール！国内線最安 1,980円〜",
        "description": "成田・関西発着の国内線が期間限定特価。早い者勝ちのタイムセール。",
        "sale_start": NOW - timedelta(days=1),
        "sale_end": NOW + timedelta(days=5),
        "travel_start": TODAY + timedelta(days=14),
        "travel_end": TODAY + timedelta(days=60),
        "discount_rate": 50,
        "min_price_jpy": 1980,
        "target_destinations": ["OKA", "CTS", "FUK", "KIX", "NRT"],
        "booking_url": "https://www.springjapan.com/ja/",
        "source": "spring_japan",
        "source_url": "https://www.springjapan.com/ja/",
        "is_verified": True,
        "external_id": f"spring-{TODAY.isoformat()}-001",
    },
    {
        "category": "flight",
        "title": "ジェットスター 旅の祭典セール 片道 2,490円〜",
        "description": "国内主要路線が最安 2,490 円〜。8 日間限定セール。",
        "sale_start": NOW - timedelta(days=2),
        "sale_end": NOW + timedelta(days=6),
        "travel_start": TODAY + timedelta(days=21),
        "travel_end": TODAY + timedelta(days=90),
        "discount_rate": 40,
        "min_price_jpy": 2490,
        "target_destinations": ["OKA", "CTS", "FUK", "NGO", "NRT", "KIX"],
        "booking_url": "https://www.jetstar.com/jp/ja/deals",
        "source": "jetstar",
        "source_url": "https://www.jetstar.com/jp/ja/deals",
        "is_verified": True,
        "external_id": f"jetstar-{TODAY.isoformat()}-001",
    },
    {
        "category": "flight",
        "title": "ピーチ 超ピーチ！片道 1,500円〜（国内線）",
        "description": "関空・那覇・札幌などの人気路線が特別価格。24 時間限定フラッシュセール。",
        "sale_start": NOW,
        "sale_end": NOW + timedelta(days=1),
        "travel_start": TODAY + timedelta(days=7),
        "travel_end": TODAY + timedelta(days=45),
        "discount_rate": 60,
        "min_price_jpy": 1500,
        "target_destinations": ["OKA", "CTS", "NRT", "KIX"],
        "booking_url": "https://www.flypeach.com/jp/ja",
        "source": "peach",
        "source_url": "https://www.flypeach.com/jp/ja",
        "is_verified": True,
        "external_id": f"peach-{TODAY.isoformat()}-001",
    },
    {
        "category": "flight",
        "title": "ANAスーパーバリュー75 GW期間",
        "description": "ゴールデンウィーク旅行を早めに予約してお得に。国内全路線対象。",
        "sale_start": NOW - timedelta(days=3),
        "sale_end": NOW + timedelta(days=10),
        "travel_start": TODAY + timedelta(days=30),
        "travel_end": TODAY + timedelta(days=75),
        "discount_rate": 30,
        "min_price_jpy": 6000,
        "target_destinations": ["OKA", "CTS", "FUK", "OIT", "KOJ", "NGO"],
        "booking_url": "https://www.ana.co.jp/ja/jp/promotions/fare/supavalue/",
        "source": "ana",
        "source_url": "https://www.ana.co.jp/",
        "is_verified": True,
        "external_id": f"ana-{TODAY.isoformat()}-001",
    },
    {
        "category": "hotel",
        "title": "楽天トラベル スーパーSALE 最大50%OFF",
        "description": "国内ホテル・旅館が最大 50% オフ。クーポン併用でさらにお得。",
        "sale_start": NOW - timedelta(days=1),
        "sale_end": NOW + timedelta(days=5),
        "travel_start": TODAY + timedelta(days=1),
        "travel_end": TODAY + timedelta(days=90),
        "discount_rate": 50,
        "min_price_jpy": 3000,
        "target_destinations": None,
        "booking_url": "https://travel.rakuten.co.jp/",
        "source": "rakuten_travel",
        "source_url": "https://travel.rakuten.co.jp/",
        "is_verified": True,
        "external_id": f"rakuten-{TODAY.isoformat()}-001",
    },
    {
        "category": "flight",
        "title": "バニラエア後継 Peach 国際線セール 台北 7,900円〜",
        "description": "関空発 台北（桃園）・香港・バンコクが特価。国際線入門に最適。",
        "sale_start": NOW - timedelta(days=1),
        "sale_end": NOW + timedelta(days=7),
        "travel_start": TODAY + timedelta(days=30),
        "travel_end": TODAY + timedelta(days=120),
        "discount_rate": 35,
        "min_price_jpy": 7900,
        "target_destinations": ["TPE", "HKG", "BKK"],
        "booking_url": "https://www.flypeach.com/jp/ja",
        "source": "peach",
        "source_url": "https://www.flypeach.com/jp/ja",
        "is_verified": True,
        "external_id": f"peach-intl-{TODAY.isoformat()}-001",
    },
    {
        "category": "package",
        "title": "JTBダイナミックパッケージ 沖縄2泊3日 29,800円〜",
        "description": "往復航空券＋ホテル込みのお得なパッケージ。5月〜6月の旅行に。",
        "sale_start": NOW - timedelta(days=2),
        "sale_end": NOW + timedelta(days=14),
        "travel_start": TODAY + timedelta(days=14),
        "travel_end": TODAY + timedelta(days=60),
        "discount_rate": 20,
        "min_price_jpy": 29800,
        "target_destinations": ["OKA"],
        "booking_url": "https://www.jtb.co.jp/",
        "source": "jtb",
        "source_url": "https://www.jtb.co.jp/",
        "is_verified": False,
        "external_id": f"jtb-{TODAY.isoformat()}-001",
    },
]


def seed():
    from urllib.parse import urlparse
    url = settings.DATABASE_URL
    parsed = urlparse(url)

    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        dbname=parsed.path.lstrip("/").split("?")[0],
        user=parsed.username,
        password=parsed.password,
        sslmode="require",
    )
    cur = conn.cursor()

    inserted = 0
    skipped = 0
    for sale in SAMPLE_SALES:
        try:
            cur.execute(
                """
                INSERT INTO sale_events (
                    id, category, title, description,
                    sale_start, sale_end, travel_start, travel_end,
                    discount_rate, min_price_jpy, target_destinations,
                    booking_url, source, source_url, is_verified, external_id
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (source, external_id) DO NOTHING
                """,
                (
                    str(uuid.uuid4()),
                    sale["category"],
                    sale["title"],
                    sale["description"],
                    sale["sale_start"],
                    sale["sale_end"],
                    sale["travel_start"],
                    sale["travel_end"],
                    sale["discount_rate"],
                    sale["min_price_jpy"],
                    psycopg2.extras.Json(sale["target_destinations"]),
                    sale["booking_url"],
                    sale["source"],
                    sale["source_url"],
                    sale["is_verified"],
                    sale["external_id"],
                ),
            )
            if cur.rowcount > 0:
                inserted += 1
                print(f"  ✓ {sale['title']}")
            else:
                skipped += 1
                print(f"  - skip (already exists): {sale['title']}")
        except Exception as e:
            print(f"  ✗ error: {sale['title']} - {e}")
            conn.rollback()

    conn.commit()
    cur.close()
    conn.close()
    print(f"\n完了: {inserted} 件挿入, {skipped} 件スキップ")


if __name__ == "__main__":
    import psycopg2.extras
    seed()
