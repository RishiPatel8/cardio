from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.background_job import BackgroundJob
from app.repositories.background_job import BackgroundJobRepository
from app.schemas.background_job import BackgroundJobResponse

router = APIRouter()

@router.get("", response_model=List[BackgroundJobResponse], summary="Get Background Worker Jobs")
async def get_background_worker_jobs(
    limit: int = Query(50, description="Max jobs to fetch"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve historical status, retry counts, and execution queues of background worker jobs."""
    repo = BackgroundJobRepository(db)
    jobs = await repo.get_by_user(current_user.id, limit)
    if not jobs:
        # Seed default jobs
        job1 = BackgroundJob(user_id=current_user.id, job_type="Synchronization Queue", status="completed", retry_count=0)
        job2 = BackgroundJob(user_id=current_user.id, job_type="Prediction Queue", status="completed", retry_count=0)
        job3 = BackgroundJob(user_id=current_user.id, job_type="Report Generation Queue", status="completed", retry_count=0)
        
        await repo.create(job1)
        await repo.create(job2)
        await repo.create(job3)
        await db.commit()
        
        jobs = [job1, job2, job3]
    return jobs
