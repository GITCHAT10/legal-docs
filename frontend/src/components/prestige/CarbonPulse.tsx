import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface CarbonPulseProps {
  data: any[];
  emissionFactor: number;
}

export const CarbonPulse: React.FC<CarbonPulseProps> = ({ data, emissionFactor }) => {
  return (
    <div className="p-6 bg-slate-900 rounded-xl border border-slate-700">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-xl font-bold text-white font-mono">Carbon Pulse</h3>
        <div className="text-xs text-slate-400 font-mono bg-slate-800 px-2 py-1 rounded">
          Factor: {emissionFactor}kg/kWh (MV Grid)
        </div>
      </div>
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="time" hide />
            <YAxis stroke="#475569" fontSize={12} />
            <Tooltip
              contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }}
              itemStyle={{ color: '#10b981' }}
            />
            <Area
              type="monotone"
              dataKey="carbon"
              stroke="#10b981"
              fill="#10b981"
              fillOpacity={0.1}
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
