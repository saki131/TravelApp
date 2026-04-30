"""
主要空港データのシードスクリプト
OpenFlights (https://openflights.org/data.html) のairports.datを使用
"""
import httpx
import csv
import io
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
import psycopg2
from urllib.parse import urlparse, parse_qs

# 主要空港のIATAコード（優先的に登録する空港）
PRIORITY_AIRPORTS = {
    # 日本
    "HND", "NRT", "KIX", "ITM", "CTS", "FUK", "OKA", "NGO",
    "SDJ", "AOJ", "KOJ", "OIT", "KMI", "NGS", "MYJ", "TAK",
    "TKS", "KCZ", "UBJ", "HIJ", "OKJ", "KMQ", "TOY", "KMJ",
    "HSG", "KKJ", "IWJ", "TSJ", "IKI", "OKI", "MMY", "ISG",
    # アジア
    "ICN", "GMP", "TPE", "TSA", "HKG", "PVG", "PEK", "SIN",
    "BKK", "DMK", "KUL", "MNL", "CGK", "HAN", "SGN", "CXR",
    "DPS", "DAD",
    # 欧州
    "LHR", "LGW", "CDG", "ORY", "AMS", "FRA", "MUC", "ZRH",
    "VIE", "FCO", "MXP", "MAD", "BCN", "LIS", "DUB", "BRU",
    "CPH", "ARN", "HEL", "OSL",
    # 北米
    "JFK", "LGA", "EWR", "LAX", "SFO", "ORD", "ATL", "DFW",
    "MIA", "SEA", "DEN", "BOS", "YYZ", "YVR",
    # 中東・オセアニア
    "DXB", "AUH", "DOH", "SYD", "MEL", "BNE",
}

# 日本語名のマッピング (iata_code -> (name_ja, city_ja, country_ja))
JA_NAMES: dict[str, tuple[str, str, str]] = {
    # 日本
    "HND": ("東京国際空港（羽田）", "東京", "日本"),
    "NRT": ("成田国際空港", "東京", "日本"),
    "KIX": ("関西国際空港", "大阪", "日本"),
    "ITM": ("大阪国際空港（伊丹）", "大阪", "日本"),
    "CTS": ("新千歳空港", "札幌", "日本"),
    "FUK": ("福岡空港", "福岡", "日本"),
    "OKA": ("那覇空港", "那覇", "日本"),
    "NGO": ("中部国際空港（セントレア）", "名古屋", "日本"),
    "SDJ": ("仙台空港", "仙台", "日本"),
    "AOJ": ("青森空港", "青森", "日本"),
    "KOJ": ("鹿児島空港", "鹿児島", "日本"),
    "OIT": ("大分空港", "大分", "日本"),
    "KMI": ("宮崎空港", "宮崎", "日本"),
    "NGS": ("長崎空港", "長崎", "日本"),
    "MYJ": ("松山空港", "松山", "日本"),
    "TAK": ("高松空港", "高松", "日本"),
    "TKS": ("徳島空港", "徳島", "日本"),
    "KCZ": ("高知空港", "高知", "日本"),
    "UBJ": ("山口宇部空港", "山口", "日本"),
    "HIJ": ("広島空港", "広島", "日本"),
    "OKJ": ("岡山空港", "岡山", "日本"),
    "KMQ": ("小松空港", "小松", "日本"),
    "TOY": ("富山空港", "富山", "日本"),
    "KMJ": ("熊本空港", "熊本", "日本"),
    "HSG": ("佐賀空港", "佐賀", "日本"),
    "KKJ": ("北九州空港", "北九州", "日本"),
    "MMY": ("宮古空港", "宮古島", "日本"),
    "ISG": ("石垣空港", "石垣島", "日本"),
    # 海外
    "ICN": ("仁川国際空港", "ソウル", "韓国"),
    "GMP": ("金浦国際空港", "ソウル", "韓国"),
    "TPE": ("台湾桃園国際空港", "台北", "台湾"),
    "TSA": ("台北松山空港", "台北", "台湾"),
    "HKG": ("香港国際空港", "香港", "香港"),
    "PVG": ("上海浦東国際空港", "上海", "中国"),
    "PEK": ("北京首都国際空港", "北京", "中国"),
    "SIN": ("チャンギ国際空港", "シンガポール", "シンガポール"),
    "BKK": ("スワンナプーム国際空港", "バンコク", "タイ"),
    "DMK": ("ドンムアン国際空港", "バンコク", "タイ"),
    "KUL": ("クアラルンプール国際空港", "クアラルンプール", "マレーシア"),
    "MNL": ("ニノイ・アキノ国際空港", "マニラ", "フィリピン"),
    "CGK": ("スカルノ・ハッタ国際空港", "ジャカルタ", "インドネシア"),
    "DPS": ("ングラ・ライ国際空港", "バリ島", "インドネシア"),
    "HAN": ("ノイバイ国際空港", "ハノイ", "ベトナム"),
    "SGN": ("タンソンニャット国際空港", "ホーチミン", "ベトナム"),
    "CXR": ("カムラン国際空港", "ニャチャン", "ベトナム"),
    "DAD": ("ダナン国際空港", "ダナン", "ベトナム"),
    "LHR": ("ヒースロー空港", "ロンドン", "イギリス"),
    "LGW": ("ガトウィック空港", "ロンドン", "イギリス"),
    "CDG": ("シャルル・ド・ゴール空港", "パリ", "フランス"),
    "ORY": ("オルリー空港", "パリ", "フランス"),
    "AMS": ("スキポール空港", "アムステルダム", "オランダ"),
    "FRA": ("フランクフルト空港", "フランクフルト", "ドイツ"),
    "MUC": ("ミュンヘン空港", "ミュンヘン", "ドイツ"),
    "ZRH": ("チューリッヒ空港", "チューリッヒ", "スイス"),
    "VIE": ("ウィーン国際空港", "ウィーン", "オーストリア"),
    "FCO": ("レオナルド・ダ・ヴィンチ国際空港", "ローマ", "イタリア"),
    "MXP": ("マルペンサ国際空港", "ミラノ", "イタリア"),
    "MAD": ("マドリード・バラハス空港", "マドリード", "スペイン"),
    "BCN": ("バルセロナ・エル・プラット空港", "バルセロナ", "スペイン"),
    "LIS": ("リスボン・ウンベルト・デルガード空港", "リスボン", "ポルトガル"),
    "DXB": ("ドバイ国際空港", "ドバイ", "UAE"),
    "AUH": ("アブダビ国際空港", "アブダビ", "UAE"),
    "DOH": ("ハマド国際空港", "ドーハ", "カタール"),
    "SYD": ("シドニー国際空港", "シドニー", "オーストラリア"),
    "MEL": ("メルボルン空港", "メルボルン", "オーストラリア"),
    "BNE": ("ブリスベン空港", "ブリスベン", "オーストラリア"),
    "JFK": ("ジョン・F・ケネディ国際空港", "ニューヨーク", "アメリカ"),
    "LAX": ("ロサンゼルス国際空港", "ロサンゼルス", "アメリカ"),
    "SFO": ("サンフランシスコ国際空港", "サンフランシスコ", "アメリカ"),
    "ORD": ("オヘア国際空港", "シカゴ", "アメリカ"),
    "ATL": ("ハーツフィールド・ジャクソン空港", "アトランタ", "アメリカ"),
    "YYZ": ("トロント・ピアソン国際空港", "トロント", "カナダ"),
    "YVR": ("バンクーバー国際空港", "バンクーバー", "カナダ"),
}

OPENFLIGHTS_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"


def seed_airports():
    print("OpenFlightsからデータを取得中...")
    import urllib.request
    with urllib.request.urlopen(OPENFLIGHTS_URL, timeout=30) as resp:
        content = resp.read().decode("utf-8")

    reader = csv.reader(io.StringIO(content))
    airports = []
    for row in reader:
        if len(row) < 8:
            continue
        iata = row[4].strip('"')
        name = row[1].strip('"')
        city = row[2].strip('"')
        country = row[3].strip('"')

        if not iata or iata == "\\N" or len(iata) != 3:
            continue
        if iata not in PRIORITY_AIRPORTS:
            continue

        ja = JA_NAMES.get(iata)
        airports.append((
            iata,
            name,
            city,
            ja[0] if ja else name,
            ja[1] if ja else city,
            country[:2].upper() if len(country) >= 2 else "??",
            ja[2] if ja else country,
        ))

    print(f"{len(airports)}件の空港データを挿入中...")

    # psycopg2 で接続（sslmode=require 対応）
    conn = psycopg2.connect(settings.DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    for ap in airports:
        cur.execute("""
            INSERT INTO airports (iata_code, name_en, city_en, name_ja, city_ja, country_code, country_ja, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
            ON CONFLICT (iata_code) DO UPDATE
            SET name_en = EXCLUDED.name_en,
                city_en = EXCLUDED.city_en,
                name_ja = EXCLUDED.name_ja,
                city_ja = EXCLUDED.city_ja,
                country_code = EXCLUDED.country_code,
                country_ja = EXCLUDED.country_ja,
                is_active = TRUE
        """, ap)

    conn.commit()
    cur.close()
    conn.close()
    print(f"完了！{len(airports)}件登録しました。")


if __name__ == "__main__":
    seed_airports()

