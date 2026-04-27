export interface ExmailStats {
  emails_sent: number;
  opens: number;
  clicks: number;
  replies: number;
  conversion_rate: number;
}

export interface Campaign {
  name: string;
  region: string;
  priority: 'HIGH' | 'NORMAL' | 'LOW';
  sent: number;
  opens: number;
  clicks: number;
  replies: number;
  status: string;
}

export interface Lead {
  id: string;
  email: string;
  name: string;
  region: string;
  priority: string;
  last_event: string;
  status: string;
}

export interface SalesTask {
  task_id: string;
  email: string;
  type: string;
  assignee: string;
  priority: string;
  status: string;
}
