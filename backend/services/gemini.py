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


FLASH_SALE_PROMPT = """
以下の航空会社・旅行会社のフラッシュセール・タイムセール情報をGoogle検索で調べ、
現在開催中または近日発表されたセール情報を JSON 形式で返してください。

調査対象: JAL, ANA, Peach, Jetstar, Spring Japan, HIS, JTB

返却形式（JSON配列のみ、前後に余分なテキスト不要）:
[
  {
    "title": "セール名",
    "category": "flight",
    "description": "セール概要（100字以内）",
    "sale_end": "YYYY-MM-DD または null",
    "travel_start": "YYYY-MM-DD または null",
    "travel_end": "YYYY-MM-DD または null",
    "min_price_jpy": 数値または null,
    "discount_rate": 数値(%)または null,
    "target_routes": null,
    "booking_url": "公式URL",
    "source": "会社名（例: peach, jetstar, ana, jal）",
    "coupon_code": null
  }
]

見つからない場合は空の配列 [] を返してください。
"""


async def detect_flash_sales() -> list[dict]:
    """Google Search グラウンディングでフラッシュセールを検知する。"""
    if not _get_api_keys():
        return []
    try:
        response = await _generate_with_key_rotation(
            model="gemini-2.0-flash-lite",
            contents=FLASH_SALE_PROMPT,
            config_obj=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.1,
            ),
        )
        raw = response.text.strip()
        # コードブロック除去
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        if not isinstance(data, list):
            return []
        return data
    except Exception as e:
        logger.error("Gemini flash sale detection failed: %s", e)
        return []


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
