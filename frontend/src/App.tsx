import { useState, useEffect } from 'react'
import { CalculatorForm } from './components/CalculatorForm'
import { ResultsDashboard } from './components/ResultsDashboard'
import { type FootprintInput, type FootprintResult, calculateFootprint } from './api'

function App() {
  const [input, setInput] = useState<FootprintInput>({
    island_id: "MV-001",
    pms: { occupancy_rooms: 0, laundry_volume_kg: 0, fn_b_procurement_usd: 0 },
    logistics: { speedboat_fuel_liters: 0, staff_travel_km: 0, guest_travel_km: 0 },
    environmental: {
        electricity_kwh: 0,
        water_m3: 0,
        lpg_kg: 0,
        plastic_waste_kg: 0,
        recycled_waste_kg: 0,
        coral_health_index: 0
    },
    social: { female_board_percent: 0, local_supplier_spend_usd: 0, community_project_spend_usd: 0 },
    governance: { sustainability_policy_active: false, internal_audit_score: 0 }
  });

  const [result, setResult] = useState<FootprintResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const controller = new AbortController();

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await calculateFootprint(input, controller.signal);
        setResult(res);
      } catch (err: any) {
        if (err.name === 'AbortError') return;
        console.error(err);
      } finally {
        if (!controller.signal.aborted) {
            setLoading(false);
        }
      }
    }, 500);

    return () => {
        clearTimeout(timer);
        controller.abort();
    };
  }, [input]);

  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl">
            Maldives <span className="text-maldives-blue">Sovereign ESG Cockpit</span>
          </h1>
          <p className="mt-3 text-base text-gray-500">
            Mandatory ESG Orchestration & Compliance (IFRS S1/S2 Alignment)
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
            <CalculatorForm input={input} setInput={setInput} />
            <div className="space-y-6 lg:sticky lg:top-8">
                {loading && <div className="text-center text-maldives-blue font-bold animate-pulse">Syncing Telemetry...</div>}
                <ResultsDashboard result={result} />
            </div>
        </div>
      </div>
    </div>
  )
}

export default App
