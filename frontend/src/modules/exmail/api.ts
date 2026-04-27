import { ExmailStats, Campaign, Lead, SalesTask } from './types';

const API_BASE = '/imoxon/exmail';

export const getExmailStats = async (): Promise<ExmailStats> => {
  const res = await fetch(`${API_BASE}/stats`);
  return res.json();
};

export const getCampaigns = async (): Promise<Campaign[]> => {
  const res = await fetch(`${API_BASE}/campaigns`);
  return res.json();
};

export const getLeadInbox = async (): Promise<Lead[]> => {
  const res = await fetch(`/imoxon/sales/leads`);
  return res.json();
};

export const getSalesTasks = async (): Promise<SalesTask[]> => {
  const res = await fetch(`/imoxon/sales/tasks?assignee=Irina Rogova`);
  return res.json();
};

export const updateLeadStatus = async (email: string, status: string) => {
  return fetch(`/imoxon/sales/leads/status`, {
    method: 'POST',
    body: JSON.stringify({ email, status })
  });
};
