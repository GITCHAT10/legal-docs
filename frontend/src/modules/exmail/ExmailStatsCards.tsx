import React from 'react';
import { ExmailStats } from './types';

const ExmailStatsCards: React.FC<{ stats: ExmailStats }> = ({ stats }) => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      <div className="p-4 bg-slate-800 rounded-lg shadow">
        <div className="text-sm text-slate-400">Emails Sent</div>
        <div className="text-2xl font-bold">{stats.emails_sent}</div>
      </div>
      <div className="p-4 bg-slate-800 rounded-lg shadow">
        <div className="text-sm text-slate-400">Open Rate</div>
        <div className="text-2xl font-bold text-blue-400">
          {((stats.opens / stats.emails_sent) * 100).toFixed(1)}%
        </div>
      </div>
      <div className="p-4 bg-slate-800 rounded-lg shadow">
        <div className="text-sm text-slate-400">Click Rate</div>
        <div className="text-2xl font-bold text-green-400">
          {((stats.clicks / stats.emails_sent) * 100).toFixed(1)}%
        </div>
      </div>
      <div className="p-4 bg-slate-800 rounded-lg shadow">
        <div className="text-sm text-slate-400">Replies</div>
        <div className="text-2xl font-bold text-purple-400">{stats.replies}</div>
      </div>
      <div className="p-4 bg-slate-800 rounded-lg shadow">
        <div className="text-sm text-slate-400">Conversion</div>
        <div className="text-2xl font-bold text-yellow-400">{stats.conversion_rate}%</div>
      </div>
    </div>
  );
};

export default ExmailStatsCards;
