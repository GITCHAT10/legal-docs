import asyncio
import pandas as pd
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def import_contacts():
    engine = create_async_engine("sqlite+aiosqlite:///exmail_kpi.db")
    df = pd.read_csv("new_contacts_validated.csv")

    async with engine.begin() as conn:
        # Ensure table exists (simplified for script)
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS outreach_tracker (
                email VARCHAR(255) PRIMARY KEY,
                company VARCHAR(255),
                region VARCHAR(50),
                country VARCHAR(50),
                agent_type VARCHAR(50),
                priority_tier VARCHAR(10),
                contact_role VARCHAR(50),
                status VARCHAR(50) DEFAULT 'not-contacted',
                trigger_segment VARCHAR(50),
                last_contact TIMESTAMPTZ,
                notes TEXT
            )
        """))

        for _, row in df.iterrows():
            await conn.execute(text("""
                INSERT OR REPLACE INTO outreach_tracker
                (email, company, region, country, agent_type, priority_tier, contact_role, status, trigger_segment)
                VALUES (:email, :company, :region, :country, :agent_type, :priority_tier, :contact_role, :status, :trigger_segment)
            """), row.to_dict())

    print(f"Imported {len(df)} contacts.")

if __name__ == "__main__":
    asyncio.run(import_contacts())
