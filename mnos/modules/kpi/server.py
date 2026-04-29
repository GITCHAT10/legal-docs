from fastapi import FastAPI, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, func, text
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta, timezone

app = FastAPI(title="EXMAIL KPI Engine")

# DB setup (replace with your actual DSN)
# Using a local sqlite for now as postgres is not available in sandbox
engine = create_async_engine("sqlite+aiosqlite:///exmail_kpi.db", echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# --- Pydantic Schemas (UI-Ready) ---
class RevenueKPI(BaseModel):
    total_gross: float
    total_net: float
    total_margin: float
    avg_margin_pct: float
    total_tax: float
    total_commission: float

class CampaignMetric(BaseModel):
    campaign_id: str
    name: str
    sent: int
    opened: int
    clicked: int
    converted: int
    ctr: float
    cvr: float
    roas: float
    avg_margin_pct: float

class FXComplianceKPI(BaseModel):
    total_usd_revenue: float
    required_conversion_usd: float
    converted_so_far_usd: float
    remaining_usd: float
    compliance_pct: float

class AttributionChain(BaseModel):
    trace_id: str
    campaign_id: str
    campaign_name: str
    email_sent: str
    email_opened: Optional[str]
    email_clicked: Optional[str]
    booking_status: Optional[str]
    gross_amount: Optional[float]
    margin_amount: Optional[float]

# --- Aggregation Endpoints ---
@app.get("/kpi/revenue", response_model=RevenueKPI)
async def get_revenue_kpi(
    start: datetime = Query(default_factory=lambda: datetime.now(timezone.utc) - timedelta(days=30)),
    end: datetime = Query(default_factory=lambda: datetime.now(timezone.utc)),
    db: AsyncSession = Depends(get_db)
):
    q = text("""
        SELECT
            SUM(gross_amount) as gross,
            SUM(net_amount) as net,
            SUM(margin_amount) as margin,
            SUM(tax_amount) as tax,
            SUM(commission_amount) as commission,
            CASE WHEN SUM(gross_amount) > 0 THEN (SUM(margin_amount)/SUM(gross_amount))*100 ELSE 0 END as margin_pct
        FROM bookings
        WHERE status = 'confirmed' AND booked_ts BETWEEN :start AND :end
    """)
    result = await db.execute(q, {"start": start, "end": end})
    row = result.first()
    return RevenueKPI(
        total_gross=float(row[0] or 0),
        total_net=float(row[1] or 0),
        total_margin=float(row[2] or 0),
        avg_margin_pct=float(row[5] or 0),
        total_tax=float(row[3] or 0),
        total_commission=float(row[4] or 0)
    )

@app.get("/kpi/campaigns", response_model=List[CampaignMetric])
async def get_campaign_metrics(
    start: datetime = Query(default_factory=lambda: datetime.now(timezone.utc) - timedelta(days=30)),
    end: datetime = Query(default_factory=lambda: datetime.now(timezone.utc)),
    db: AsyncSession = Depends(get_db)
):
    q = text("""
        WITH funnel AS (
            SELECT
                c.campaign_id, c.name,
                COUNT(CASE WHEN e.event_type='sent' THEN 1 END) as sent,
                COUNT(CASE WHEN e.event_type='opened' THEN 1 END) as opened,
                COUNT(CASE WHEN e.event_type='clicked' THEN 1 END) as clicked,
                COUNT(CASE WHEN e.event_type='converted' THEN 1 END) as converted,
                COALESCE(SUM(b.gross_amount), 0) as revenue,
                CASE WHEN SUM(b.gross_amount) > 0 THEN (SUM(b.margin_amount)/SUM(b.gross_amount))*100 ELSE 0 END as margin_pct
            FROM campaigns c
            LEFT JOIN email_events e ON c.campaign_id = e.campaign_id
                AND e.event_ts BETWEEN :start AND :end
            LEFT JOIN bookings b ON e.trace_id = b.trace_id AND b.status='confirmed'
            GROUP BY c.campaign_id, c.name
        )
        SELECT *,
            CASE WHEN opened > 0 THEN (CAST(clicked AS FLOAT)/opened)*100 ELSE 0 END as ctr,
            CASE WHEN clicked > 0 THEN (CAST(converted AS FLOAT)/clicked)*100 ELSE 0 END as cvr,
            CASE WHEN sent > 0 THEN revenue / NULLIF(sent, 0) ELSE 0 END as roas
        FROM funnel
    """)
    result = await db.execute(q, {"start": start, "end": end})
    rows = result.fetchall()
    return [CampaignMetric(
        campaign_id=r[0], name=r[1], sent=r[2] or 0, opened=r[3] or 0,
        clicked=r[4] or 0, converted=r[5] or 0, ctr=float(r[8]),
        cvr=float(r[9]), roas=float(r[10]), avg_margin_pct=float(r[7])
    ) for r in rows]

@app.get("/kpi/fx-compliance", response_model=FXComplianceKPI)
async def get_fx_compliance(db: AsyncSession = Depends(get_db)):
    # 1. Get total USD revenue from bookings
    # (Note: In this schema, net_amount is MVR, we need USD base)
    # For simulation, we assume base_usd is stored in a structured way or we aggregate
    usd_q = text("SELECT SUM(gross_amount) FROM bookings WHERE status = 'confirmed'")
    usd_res = await db.execute(usd_q)
    total_usd = float(usd_res.scalar() or 0)

    # 2. Get converted amount from fx_conversions
    conv_q = text("SELECT SUM(usd_amount) FROM fx_conversions")
    conv_res = await db.execute(conv_q)
    converted = float(conv_res.scalar() or 0)

    required = total_usd * 0.20
    remaining = max(0, required - converted)

    return FXComplianceKPI(
        total_usd_revenue=total_usd,
        required_conversion_usd=required,
        converted_so_far_usd=converted,
        remaining_usd=remaining,
        compliance_pct=(converted / required * 100) if required > 0 else 100.0
    )

@app.get("/kpi/attribution/{trace_id}", response_model=Optional[AttributionChain])
async def get_attribution(trace_id: str, db: AsyncSession = Depends(get_db)):
    q = text("""
        SELECT
            e.campaign_id, c.name,
            MAX(CASE WHEN e.event_type='sent' THEN e.event_ts END),
            MAX(CASE WHEN e.event_type='opened' THEN e.event_ts END),
            MAX(CASE WHEN e.event_type='clicked' THEN e.event_ts END),
            b.status, b.gross_amount, b.margin_amount
        FROM email_events e
        JOIN campaigns c ON e.campaign_id = c.campaign_id
        LEFT JOIN bookings b ON e.trace_id = b.trace_id
        WHERE e.trace_id = :tid
        GROUP BY e.campaign_id, c.name, b.status, b.gross_amount, b.margin_amount
    """)
    result = await db.execute(q, {"tid": trace_id})
    row = result.first()
    if not row:
         return None
    return AttributionChain(
        trace_id=trace_id, campaign_id=row[0], campaign_name=row[1],
        email_sent=str(row[2]), email_opened=str(row[3]) if row[3] else None,
        email_clicked=str(row[4]) if row[4] else None,
        booking_status=row[5], gross_amount=float(row[6]) if row[6] else None,
        margin_amount=float(row[7]) if row[7] else None
    )
