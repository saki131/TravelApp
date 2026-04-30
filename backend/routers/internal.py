"""
内部エンドポイント（Cloud Scheduler から呼び出す）
認証: X-API-Key（PERSONAL_API_KEY）
"""
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException

from dependencies import verify_api_key
from scheduler.jobs import job_collect_rss, job_gemini_grounding, job_cleanup

router = APIRouter(prefix="/internal", tags=["internal"])
logger = logging.getLogger(__name__)

JOBS = {
    "collect-rss":       job_collect_rss,
    "collect-sales":     job_gemini_grounding,
    "cleanup":           job_cleanup,
}


@router.post("/jobs/{job_name}", dependencies=[Depends(verify_api_key)])
async def trigger_job(job_name: str):
    """Cloud Scheduler から呼び出される定期ジョブのトリガー。"""
    job_fn = JOBS.get(job_name)
    if not job_fn:
        raise HTTPException(status_code=404, detail=f"Job '{job_name}' not found")

    logger.info("Triggering job: %s", job_name)
    if asyncio.iscoroutinefunction(job_fn):
        await job_fn()
    else:
        job_fn()
    return {"job": job_name, "status": "completed"}
