import asyncio
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from ..models.allotment import AllotmentBlock
from ..models.contract import VendorContract, ContractStatus
import structlog

logger = structlog.get_logger()

class AllotmentEngine:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def check_and_reserve(self, contract_id: str, dates: list[date], units: int, trace_id: str) -> bool:
        for d in dates:
            stmt = (
                select(AllotmentBlock)
                .where(
                    AllotmentBlock.contract_id == contract_id,
                    AllotmentBlock.start_date <= d,
                    AllotmentBlock.end_date >= d,
                    AllotmentBlock.total_units - AllotmentBlock.reserved_units >= units
                )
                .with_for_update()  # DB-level row lock
            )
            result = await self.db.execute(stmt)
            block = result.scalar_one_or_none()
            if not block:
                logger.warning("insufficient_allotment", contract_id=contract_id, date=d)
                return False

            # Atomic decrement + version bump
            await self.db.execute(
                update(AllotmentBlock)
                .where(AllotmentBlock.block_id == block.block_id, AllotmentBlock.version == block.version)
                .values(reserved_units=AllotmentBlock.reserved_units + units, version=AllotmentBlock.version + 1)
            )

        await self.db.commit()
        logger.info("allotment_reserved", trace_id=trace_id, contract_id=contract_id, units=units)
        return True

    async def release(self, contract_id: str, dates: list[date], units: int, trace_id: str):
        for d in dates:
            stmt = select(AllotmentBlock).where(
                AllotmentBlock.contract_id == contract_id,
                AllotmentBlock.start_date <= d,
                AllotmentBlock.end_date >= d
            ).with_for_update()
            result = await self.db.execute(stmt)
            block = result.scalar_one_or_none()
            if block:
                await self.db.execute(
                    update(AllotmentBlock)
                    .where(AllotmentBlock.block_id == block.block_id)
                    .values(reserved_units=max(0, block.reserved_units - units))
                )
        await self.db.commit()
        logger.info("allotment_released", trace_id=trace_id, contract_id=contract_id, units=units)
