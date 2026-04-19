import { useState, useEffect } from 'react'
import { CalculatorForm } from './components/CalculatorForm'
import { ResultsDashboard } from './components/ResultsDashboard'
import { type FootprintInput, type FootprintResult, calculateFootprint } from './api'

function App() {
  const [input, setInput] = useState<FootprintInput>({
    home: { electricity_kwh: 0, water_m3: 0, lpg_kg: 0 },
    transport: {
      petrol_car_km: 0,
      diesel_car_km: 0,
      motorcycle_km: 0,
      speedboat_liters: 0,
      ferry_km: 0,
      seaplane_km: 0,
      domestic_flight_km: 0
    },
    waste: { waste_kg: 0 }
  });

  const [result, setResult] = useState<FootprintResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await calculateFootprint(input);
        setResult(res);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [input]);

  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl">
            Maldives <span className="text-maldives-blue">Carbon Engine</span>
          </h1>
          <p className="mt-3 text-base text-gray-500">
            Calculate your environmental impact in the Sunny Side of Life.
          </p>
        </div>

        <CalculatorForm input={input} setInput={setInput} />

        {loading && <div className="text-center text-maldives-blue font-bold">Calculating...</div>}

        <ResultsDashboard result={result} />
      </div>
    </div>
  )
}

export default App
