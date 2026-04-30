"""
AI 旅行プランナー ルーター（F-08）
"""
from typing import Optional
from pydantic import BaseModel

from fastapi import APIRouter, Depends

from dependencies import verify_api_key
from services.gemini import generate_travel_plan

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


class PlanRequest(BaseModel):
    origin: str
    budget_jpy: int
    days: int
    style: str          # beach | city | nature | gourmet
    flight_info: Optional[dict] = None


@router.post("/plan", dependencies=[Depends(verify_api_key)])
async def generate_plan(req: PlanRequest):
    """Gemini Flash で旅行プランを生成する。"""
    plan_text = await generate_travel_plan(
        origin=req.origin,
        budget_jpy=req.budget_jpy,
        days=req.days,
        style=req.style,
        flight_info=req.flight_info,
    )
    return {"plan": plan_text}
