export interface FootprintInput {
  home?: {
    electricity_kwh: number;
    water_m3: number;
    lpg_kg: number;
  };
  transport?: {
    petrol_car_km: number;
    diesel_car_km: number;
    motorcycle_km: number;
    speedboat_liters: number;
    ferry_km: number;
    seaplane_km: number;
    domestic_flight_km: number;
  };
  waste?: {
    waste_kg: number;
  };
}

export interface FootprintResult {
  home_total: number;
  transport_total: number;
  waste_total: number;
  grand_total: number;
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
    throw new Error('Failed to calculate footprint');
  }

  return response.json();
}
