"""
Gemini Flash ラッパー
- AI 旅行プランナー
- Google Search グラウンディング（セール検知）
"""
import asyncio
import itertools
import json
import logging
from typing import Optional

from google import genai
from google.genai import types

from config import settings

logger = logging.getLogger(__name__)

# ラウンドロビン用カウンター
_key_counter = itertools.count()


def _get_api_keys() -> list[str]:
    """設定済みの Gemini API キーをリストで返す（空キーは除外）"""
    keys = [
        settings.GEMINI_API_KEY,
        settings.GEMINI_API_KEY_2,
        settings.GEMINI_API_KEY_3,
    ]
    return [k for k in keys if k]


async def _generate_with_key_rotation(model: str, contents, config_obj=None):
    """
    ラウンドロビンで API キーを均等分散し、
    レート制限(429)時は自動的に次のキーへフォールバック。
    """
    keys = _get_api_keys()
    if not keys:
        raise RuntimeError("Gemini API キーが設定されていません")

    start = next(_key_counter) % len(keys)
    ordered = keys[start:] + keys[:start]

    last_exc: Exception = RuntimeError("unknown")
    for i, key in enumerate(ordered):
        key_num = keys.index(key) + 1
        client = genai.Client(api_key=key)
        try:
            logger.info("Gemini API 呼び出し: キー%d/%d, model=%s", key_num, len(keys), model)
            kwargs = dict(model=model, contents=contents)
            if config_obj is not None:
                kwargs["config"] = config_obj
            resp = client.models.generate_content(**kwargs)
            logger.info("Gemini API 成功: キー%d", key_num)
            return resp
        except Exception as e:
            last_exc = e
            err_str = str(e)
            is_rate = (
                "429" in err_str
                or "RATE_LIMIT" in err_str
                or "quota" in err_str.lower()
                or "RESOURCE_EXHAUSTED" in err_str
            )
            if is_rate and i < len(ordered) - 1:
                logger.warning("Gemini キー%d がレート制限、次のキーへ切替", key_num)
                continue
            raise
    raise last_exc


def _make_sale_prompt(source: str, airline_name: str, query_hint: str) -> str:
    return f"""
今日の日付は {__import__('datetime').date.today()} です。
Google検索で「{query_hint}」を調べ、**現在開催中または近日開催予定**のセール・タイムセール情報を探してください。

必ず公式サイト（{airline_name}の公式ドメイン）の情報を優先して参照してください。

見つかった情報を以下のJSON配列のみで返してください（前後に説明文不要）:
[
  {{
    "title": "セール名（公式サイトの表記に合わせる）",
    "category": "flight",
    "description": "セール概要（150字以内、予約期間・搭乗期間・対象路線を含める）",
    "sale_start": "予約受付開始日 YYYY-MM-DD、不明なら null",
    "sale_end": "予約締切日 YYYY-MM-DD、不明なら null",
    "travel_start": "搭乗・旅行開始日 YYYY-MM-DD、不明なら null",
    "travel_end": "搭乗・旅行終了日 YYYY-MM-DD、不明なら null",
    "min_price_jpy": 片道最低価格（整数・円）または null,
    "discount_rate": 割引率（整数・%）または null,
    "booking_url": "セールページの公式URL",
    "source": "{source}",
    "coupon_code": "クーポンコードまたは null"
  }}
]

セール情報が見つからない場合は [] を返してください。
日付が明記されていない場合は必ず null にしてください（推測で埋めないこと）。
"""


# 航空会社ごとの検索ヒント
_AIRLINE_TARGETS = [
    ("peach",        "Peach Aviation",  "ピーチ タイムセール 予約期間 搭乗期間 site:flypeach.com"),
    ("jetstar",      "Jetstar Japan",   "ジェットスター セール 予約期間 搭乗期間 site:jetstar.com"),
    ("spring_japan", "Spring Japan",    "スプリングジャパン セール 予約期間 搭乗期間 site:ch.com OR site:spring-japan.co.jp"),
    ("jal",          "JAL",             "JAL タイムセール 特割 予約期間 搭乗期間 site:jal.co.jp"),
    ("ana",          "ANA",             "ANA タイムセール スーパーバリュー 予約期間 搭乗期間 site:ana.co.jp"),
]


async def detect_flash_sales() -> list[dict]:
    """Gemini Google Search グラウンディングで航空会社ごとにセールを検索する。"""
    if not _get_api_keys():
        return []

    all_results: list[dict] = []
    for source, airline_name, query_hint in _AIRLINE_TARGETS:
        prompt = _make_sale_prompt(source, airline_name, query_hint)
        try:
            response = await _generate_with_key_rotation(
                model="gemini-2.0-flash",
                contents=prompt,
                config_obj=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    temperature=0.0,
                ),
            )
            raw = response.text.strip()
            # コードブロック除去
            if "```" in raw:
                parts = raw.split("```")
                raw = parts[1] if len(parts) > 1 else parts[0]
                if raw.startswith("json"):
                    raw = raw[4:]
            # JSON部分だけ抽出
            s = raw.find("[")
            e = raw.rfind("]")
            if s != -1 and e != -1:
                raw = raw[s:e+1]
            data = json.loads(raw)
            if isinstance(data, list):
                logger.info("Gemini sale detect [%s]: %d件", source, len(data))
                all_results.extend(data)
        except Exception as ex:
            logger.warning("Gemini sale detect [%s] failed: %s", source, ex)

    return all_results


async def generate_travel_plan(
    origin: str,
    budget_jpy: int,
    days: int,
    style: str,
    flight_info: Optional[dict] = None,
) -> str:
    """AI 旅行プランを生成する（Markdown テキストを返す）。"""
    if not _get_api_keys():
        return "AI 機能が現在利用できません（APIキー未設定）。"

    flight_context = ""
    if flight_info:
        flight_context = f"\n利用可能なフライト:\n{json.dumps(flight_info, ensure_ascii=False, indent=2)}"

    prompt = f"""
あなたは日本語対応の旅行プランナーです。以下の条件で旅行計画を作成してください。

出発地: {origin}
予算: ¥{budget_jpy:,}（往復交通費込み）
日数: {days}日間
旅行スタイル: {style}
{flight_context}

以下の内容を含む Markdown 形式のプランを作成してください:
1. おすすめ行き先（2〜3候補）と選んだ理由
2. 詳細な日程（Day 1 〜 Day N）
   - 観光スポット・グルメ・移動手段
3. 予算内訳（フライト・ホテル・食事・観光）
4. 現地での必須情報（通貨・言語・注意事項）

実際に行動できる具体的な内容を心がけてください。
"""
    try:
        response = await _generate_with_key_rotation(
            model="gemini-2.0-flash-lite",
            contents=prompt,
            config_obj=types.GenerateContentConfig(temperature=0.7),
        )
        return response.text
    except Exception as e:
        logger.error("Gemini travel plan generation failed: %s", e)
        return "プランの生成に失敗しました。しばらく後にもう一度お試しください。"
