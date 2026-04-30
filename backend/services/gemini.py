"""
Gemini Flash ラッパー
- AI 旅行プランナー
- Google Search グラウンディング（セール検知）
"""
import json
import logging
from typing import Optional

import google.generativeai as genai

from config import settings

logger = logging.getLogger(__name__)

FLASH_SALE_PROMPT = """
以下の航空会社・旅行会社のフラッシュセール・タイムセール情報をGoogle検索で調べ、
現在開催中または本日発表されたセール情報を JSON 形式で返してください。

調査対象: JAL, ANA, Peach, Jetstar, Spring Japan, HIS, JTB

返却形式（JSON配列）:
[
  {{
    "title": "セール名",
    "category": "flight|hotel|package",
    "description": "セール概要（100字以内）",
    "sale_end": "YYYY-MM-DD または null",
    "travel_start": "YYYY-MM-DD または null",
    "travel_end": "YYYY-MM-DD または null",
    "min_price_jpy": 数値または null,
    "discount_rate": 数値(%)または null,
    "target_routes": ["HND-OKA"] または null,
    "booking_url": "公式URL",
    "source": "会社名",
    "coupon_code": "コードまたは null"
  }}
]

見つからない場合は空の配列 [] を返してください。
"""


def _init_model():
    if not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY が未設定のため Gemini 機能は無効です")
        return None
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=genai.GenerationConfig(
            temperature=0.1,
            response_mime_type="application/json",
        ),
    )


_model: Optional[object] = None


def get_model():
    global _model
    if _model is None:
        _model = _init_model()
    return _model


async def detect_flash_sales() -> list[dict]:
    """Google Search グラウンディングでフラッシュセールを検知する。"""
    model = get_model()
    if model is None:
        return []
    try:
        response = model.generate_content(
            FLASH_SALE_PROMPT,
            tools=[{"google_search_retrieval": {}}],
        )
        raw = response.text.strip()
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
    model = get_model()
    if model is None:
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
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error("Gemini travel plan generation failed: %s", e)
        return "プランの生成に失敗しました。しばらく後にもう一度お試しください。"
