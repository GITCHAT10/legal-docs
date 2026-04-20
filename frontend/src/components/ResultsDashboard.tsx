import React from 'react';
import { type FootprintResult } from '../api';

interface Props {
  result: FootprintResult | null;
}

export const ResultsDashboard: React.FC<Props> = ({ result }) => {
  if (!result) return null;

  return (
    <div className="space-y-4">
      <div className="bg-maldives-blue text-white p-6 rounded-lg shadow-xl">
        <h2 className="text-2xl font-bold mb-4">ESG Scoring Dashboard</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white/10 p-4 rounded-lg">
            <p className="text-sm opacity-80">Carbon / Occupied Room</p>
            <p className="text-4xl font-black">{result.carbon_per_occupied_room} kg CO₂</p>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between border-b border-white/20 pb-1">
              <span>Grand Total</span>
              <span className="font-bold">{result.grand_total} kg</span>
            </div>
            <div className="flex justify-between border-b border-white/20 pb-1">
              <span>Compliance</span>
              <span className="font-bold text-yellow-300">{result.compliance_status}</span>
            </div>
            <div className="flex justify-between">
              <span>Coral Health</span>
              <span className="font-bold">{result.metrics.coral_health} index</span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-gray-800 text-green-400 p-4 rounded-lg font-mono text-xs break-all overflow-hidden">
        <p className="text-gray-400 mb-1 uppercase tracking-widest">Shadow Ledger Hash (Immutable Evidence)</p>
        {result.shadow_hash}
      </div>
    </div>
  );
};
