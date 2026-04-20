from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from mnos.core.api import deps
from mnos.modules.inn.housekeeping import schemas, models
from mnos.core.events.dispatcher import event_dispatcher

router = APIRouter()

@router.post("/", response_model=schemas.HousekeepingTask)
def create_task(
    *,
    db: Session = Depends(deps.get_db),
    task_in: schemas.HousekeepingTaskCreate,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    db_obj = models.HousekeepingTask(**task_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/", response_model=List[schemas.HousekeepingTask])
def read_tasks(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    return db.query(models.HousekeepingTask).offset(skip).limit(limit).all()

@router.patch("/{task_id}", response_model=schemas.HousekeepingTask)
def update_task(
    task_id: int,
    update_in: schemas.HousekeepingTaskUpdate,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    db_obj = db.query(models.HousekeepingTask).filter(models.HousekeepingTask.id == task_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Task not found")

    if update_in.status:
        db_obj.status = update_in.status
        if update_in.status == models.TaskStatus.COMPLETED:
            db_obj.completed_at = datetime.utcnow()
            event_dispatcher.dispatch("housekeeping_completed", {"room_id": db_obj.room_id, "task_id": db_obj.id})

    if update_in.assigned_to:
        db_obj.assigned_to = update_in.assigned_to

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
