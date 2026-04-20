import React from 'react';
import { type FootprintInput } from '../api';

interface Props {
  input: FootprintInput;
  setInput: React.Dispatch<React.SetStateAction<FootprintInput>>;
}

export const CalculatorForm: React.FC<Props> = ({ setInput }) => {
  const handleNestedChange = (category: keyof FootprintInput, field: string, value: any) => {
    setInput(prev => ({
      ...prev,
      [category]: { ...(prev[category] as any), [field]: value }
    }));
  };

  return (
    <div className="space-y-8 bg-white p-6 rounded-lg shadow-md">
      <section>
        <h2 className="text-xl font-bold text-maldives-blue mb-4 border-b pb-2">Environmental (IFRS S2)</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Electricity (kWh)</label>
            <input type="number" onChange={(e) => handleNestedChange('environmental', 'electricity_kwh', parseFloat(e.target.value) || 0)} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-maldives-blue focus:ring-maldives-blue" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Water (m³)</label>
            <input type="number" onChange={(e) => handleNestedChange('environmental', 'water_m3', parseFloat(e.target.value) || 0)} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-maldives-blue focus:ring-maldives-blue" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Coral Health (0-1 Index)</label>
            <input type="number" step="0.1" onChange={(e) => handleNestedChange('environmental', 'coral_health_index', parseFloat(e.target.value) || 0)} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-maldives-blue focus:ring-maldives-blue" />
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-xl font-bold text-maldives-blue mb-4 border-b pb-2">Logistics & PMS</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Daily Occupied Rooms</label>
            <input type="number" onChange={(e) => handleNestedChange('pms', 'occupancy_rooms', parseInt(e.target.value) || 0)} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-maldives-blue focus:ring-maldives-blue" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Speedboat Petrol (Liters)</label>
            <input type="number" onChange={(e) => handleNestedChange('logistics', 'speedboat_fuel_liters', parseFloat(e.target.value) || 0)} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-maldives-blue focus:ring-maldives-blue" />
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-xl font-bold text-maldives-blue mb-4 border-b pb-2">Social & Governance (IFRS S1)</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Female Board Representation (%)</label>
            <input type="number" onChange={(e) => handleNestedChange('social', 'female_board_percent', parseFloat(e.target.value) || 0)} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-maldives-blue focus:ring-maldives-blue" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Local Supplier Spend (USD)</label>
            <input type="number" onChange={(e) => handleNestedChange('social', 'local_supplier_spend_usd', parseFloat(e.target.value) || 0)} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-maldives-blue focus:ring-maldives-blue" />
          </div>
        </div>
      </section>
    </div>
  );
};
