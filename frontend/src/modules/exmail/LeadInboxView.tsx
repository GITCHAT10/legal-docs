import React, { useEffect, useState } from 'react';
import { getLeadInbox } from './api';
import { Lead } from './types';

const LeadInboxView: React.FC = () => {
  const [leads, setLeads] = useState<Lead[]>([]);

  useEffect(() => {
    getLeadInbox().then(setLeads);
  }, []);

  return (
    <div className="bg-slate-800 rounded-lg overflow-hidden">
      <table className="w-full text-left">
        <thead>
          <tr className="bg-slate-700/50">
            <th className="p-3 text-sm font-semibold">Lead / Operator</th>
            <th className="p-3 text-sm font-semibold">Region</th>
            <th className="p-3 text-sm font-semibold">Priority</th>
            <th className="p-3 text-sm font-semibold">Status</th>
            <th className="p-3 text-sm font-semibold">Audit</th>
          </tr>
        </thead>
        <tbody>
          {leads.map(lead => (
            <tr key={lead.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
              <td className="p-3">
                <div className="font-medium">{lead.name}</div>
                <div className="text-xs text-slate-400">{lead.email}</div>
              </td>
              <td className="p-3 text-sm">{lead.region}</td>
              <td className="p-3">
                <span className={`text-xs ${lead.priority === 'HIGH' ? 'text-red-400' : 'text-slate-400'}`}>
                  {lead.priority}
                </span>
              </td>
              <td className="p-3 text-sm font-bold text-blue-400">{lead.status}</td>
              <td className="p-3">
                <span className="px-1.5 py-0.5 text-[10px] bg-blue-900/30 text-blue-300 border border-blue-800 rounded uppercase">
                  SHADOW SEALED
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default LeadInboxView;
