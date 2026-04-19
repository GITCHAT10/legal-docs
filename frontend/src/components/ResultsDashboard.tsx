import React from 'react';
import { type FootprintResult } from '../api';

interface Props {
  result: FootprintResult | null;
}

export const ResultsDashboard: React.FC<Props> = ({ result }) => {
  if (!result) return null;

  return (
    <div className="bg-maldives-blue text-white p-6 rounded-lg shadow-xl">
      <h2 className="text-2xl font-bold mb-4">Your Carbon Footprint</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white/10 p-4 rounded-lg">
          <p className="text-sm opacity-80">Total Emissions</p>
          <p className="text-4xl font-black">{result.grand_total} kg CO₂</p>
        </div>
        <div className="space-y-2">
          <div className="flex justify-between border-b border-white/20 pb-1">
            <span>Home</span>
            <span className="font-bold">{result.home_total} kg</span>
          </div>
          <div className="flex justify-between border-b border-white/20 pb-1">
            <span>Transport</span>
            <span className="font-bold">{result.transport_total} kg</span>
          </div>
          <div className="flex justify-between">
            <span>Waste</span>
            <span className="font-bold">{result.waste_total} kg</span>
          </div>
        </div>
      </div>
      <p className="mt-6 text-sm italic opacity-90">
        Factors are tailored for the Maldives diesel-based grid and island logistics.
      </p>
    </div>
  );
};
