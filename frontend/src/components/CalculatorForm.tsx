import React from 'react';
import { type FootprintInput } from '../api';

interface Props {
  input: FootprintInput;
  setInput: React.Dispatch<React.SetStateAction<FootprintInput>>;
}

export const CalculatorForm: React.FC<Props> = ({ setInput }) => {
  const handleHomeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setInput(prev => ({
      ...prev,
      home: prev.home ? { ...prev.home, [name]: parseFloat(value) || 0 } : undefined
    }));
  };

  const handleTransportChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setInput(prev => ({
      ...prev,
      transport: prev.transport ? { ...prev.transport, [name]: parseFloat(value) || 0 } : undefined
    }));
  };

  const handleWasteChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { value } = e.target;
    setInput(prev => ({
      ...prev,
      waste: { waste_kg: parseFloat(value) || 0 }
    }));
  };

  return (
    <div className="space-y-8 bg-white p-6 rounded-lg shadow-md">
      <section>
        <h2 className="text-xl font-bold text-maldives-blue mb-4">Home Energy & Water</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Electricity (kWh)</label>
            <input type="number" name="electricity_kwh" onChange={handleHomeChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-maldives-blue focus:ring-maldives-blue" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Water (m³)</label>
            <input type="number" name="water_m3" onChange={handleHomeChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-maldives-blue focus:ring-maldives-blue" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Cooking Gas (LPG kg)</label>
            <input type="number" name="lpg_kg" onChange={handleHomeChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-maldives-blue focus:ring-maldives-blue" />
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-xl font-bold text-maldives-blue mb-4">Maldives Transport</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Speedboat Petrol (Liters)</label>
            <input type="number" name="speedboat_liters" onChange={handleTransportChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-maldives-blue focus:ring-maldives-blue" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Seaplane Travel (km)</label>
            <input type="number" name="seaplane_km" onChange={handleTransportChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-maldives-blue focus:ring-maldives-blue" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Domestic Flight (km)</label>
            <input type="number" name="domestic_flight_km" onChange={handleTransportChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-maldives-blue focus:ring-maldives-blue" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Ferry Travel (km)</label>
            <input type="number" name="ferry_km" onChange={handleTransportChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-maldives-blue focus:ring-maldives-blue" />
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-xl font-bold text-maldives-blue mb-4">Waste Management</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Daily Waste (kg)</label>
            <input type="number" name="waste_kg" onChange={handleWasteChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-maldives-blue focus:ring-maldives-blue" />
          </div>
        </div>
      </section>
    </div>
  );
};
