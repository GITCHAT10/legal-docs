from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from mnos.modules.ut_simulation.engine import sim_engine
from mnos.modules.ut_simulation.waterfall import waterfall_sim
from decimal import Decimal

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    # Simulated view for Minister/Investor
    sim_data = await sim_engine.run_simulation()
    waterfall = waterfall_sim.calculate_waterfall(Decimal("150000.00"))

    return f"""
    <html>
        <head><title>UT SOVEREIGN COMMAND TOWER</title></head>
        <body>
            <h1>NATIONAL DIGITAL TWIN: UNITED TRANSFER ASI</h1>
            <div>STATUS: {sim_data['status']}</div>
            <div>LOAD FACTOR: {sim_data['load_factor'] * 100}%</div>

            <h2>FINANCIAL WATERFALL (MVR)</h2>
            <ul>
                <li>GROSS: {waterfall['gross']}</li>
                <li>TAX (17%): {waterfall['tax']}</li>
                <li>NET: {waterfall['net']}</li>
            </ul>
        </body>
    </html>
    """
