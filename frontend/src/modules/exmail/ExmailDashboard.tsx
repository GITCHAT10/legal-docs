import React, { useEffect, useState } from 'react';
import { getExmailStats } from './api';
import { ExmailStats } from './types';
import ExmailStatsCards from './ExmailStatsCards';
import CampaignsView from './CampaignsView';
import LeadInboxView from './LeadInboxView';
import SalesTasksView from './SalesTasksView';

const ExmailDashboard: React.FC = () => {
  const [stats, setStats] = useState<ExmailStats | null>(null);

  useEffect(() => {
    getExmailStats().then(setStats);
  }, []);

  return (
    <div className="p-6 bg-slate-900 text-white min-h-screen">
      <header className="mb-8">
        <h1 className="text-3xl font-bold">AIR MAIL / EXMAIL</h1>
        <p className="text-slate-400">Sovereign Communication Command</p>
      </header>

      {stats && <ExmailStatsCards stats={stats} />}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
        <section>
          <h2 className="text-xl font-semibold mb-4">Active Campaigns</h2>
          <CampaignsView />
        </section>
        <section>
          <h2 className="text-xl font-semibold mb-4">Irina's Sales Tasks</h2>
          <SalesTasksView />
        </section>
      </div>

      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-4">Partner Lead Inbox</h2>
        <LeadInboxView />
      </div>
    </div>
  );
};

export default ExmailDashboard;
