export interface FootprintInput {
  island_id: string;
  pms?: {
    occupancy_rooms: number;
    laundry_volume_kg: number;
    fn_b_procurement_usd: number;
  };
  logistics?: {
    speedboat_fuel_liters: number;
    staff_travel_km: number;
    guest_travel_km: number;
  };
  environmental?: {
    electricity_kwh: number;
    water_m3: number;
    lpg_kg: number;
    plastic_waste_kg: number;
    recycled_waste_kg: number;
    coral_health_index: number;
  };
  social?: {
    female_board_percent: number;
    local_supplier_spend_usd: number;
    community_project_spend_usd: number;
  };
  governance?: {
    sustainability_policy_active: boolean;
    internal_audit_score: number;
  };
}

export interface FootprintResult {
  home_total: number;
  transport_total: number;
  waste_total: number;
  carbon_per_occupied_room: number;
  grand_total: number;
  shadow_hash: string;
  compliance_status: string;
  metrics: {
    coral_health: number;
    local_spend_percent: number;
  };
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function calculateFootprint(data: FootprintInput, signal?: AbortSignal): Promise<FootprintResult> {
  const response = await fetch(`${API_URL}/api/calculate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
    signal,
  });

  if (!response.ok) {
    if (response.statusText === 'abort') {
        throw new Error('Request aborted');
    }
    throw new Error('Failed to calculate ESG score');
  }

  return response.json();
}
