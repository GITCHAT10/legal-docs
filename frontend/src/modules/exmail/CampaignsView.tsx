import React, { useEffect, useState } from 'react';
import { getCampaigns } from './api';
import { Campaign } from './types';

const CampaignsView: React.FC = () => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);

  useEffect(() => {
    getCampaigns().then(setCampaigns);
  }, []);

  return (
    <div className="overflow-x-auto bg-slate-800 rounded-lg">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-slate-700">
            <th className="p-3">Campaign</th>
            <th className="p-3">Region</th>
            <th className="p-3">Sent</th>
            <th className="p-3">Replies</th>
            <th className="p-3">Status</th>
          </tr>
        </thead>
        <tbody>
          {campaigns.map((c, i) => (
            <tr key={i} className="border-b border-slate-700/50 hover:bg-slate-700/30">
              <td className="p-3 font-medium">{c.name}</td>
              <td className="p-3 text-sm">{c.region}</td>
              <td className="p-3 text-sm">{c.sent}</td>
              <td className="p-3 text-sm text-purple-400">{c.replies}</td>
              <td className="p-3">
                <span className="px-2 py-1 text-xs rounded bg-green-900/50 text-green-400 border border-green-700">
                  {c.status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default CampaignsView;
