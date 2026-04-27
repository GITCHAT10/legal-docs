from fastapi import APIRouter
from united_transfer_system.api.v1_router import api_v1_router

router = APIRouter()
router.include_router(api_v1_router)
