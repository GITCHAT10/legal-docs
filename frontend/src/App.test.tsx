// @vitest-environment jsdom
import { StrictMode } from 'react';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import App from './App';
import { calculateFootprint, type FootprintResult } from './api';
vi.mock('./api', () => ({ calculateFootprint: vi.fn() }));
const requests: { signal?: AbortSignal; resolve: (value: FootprintResult) => void; reject: (reason: Error) => void }[] = [];
const result = (n: number): FootprintResult => ({ home_total:n, transport_total:0, waste_total:0, carbon_per_occupied_room:n, grand_total:n, shadow_hash:`hash-${n}`, compliance_status:'PENDING', metrics:{coral_health:0,local_spend_percent:0} });
const tick = () => act(async () => { vi.advanceTimersByTime(500); });
const edit = () => fireEvent.change(screen.getAllByRole('spinbutton')[0], {target:{value:'20'}});
const resolve = (i:number,n:number) => act(async()=> { requests[i].resolve(result(n)); });
beforeEach(()=>{ vi.useFakeTimers(); requests.length=0; vi.mocked(calculateFootprint).mockImplementation((_input,signal)=>new Promise((resolve,reject)=>requests.push({signal,resolve,reject}))); });
afterEach(()=>{ cleanup(); vi.useRealTimers(); vi.restoreAllMocks(); });
it('keeps B when canceled A resolves after B, even when transport ignores abort',async()=>{
 render(<App/>); await tick(); edit(); await tick();
 expect(requests[0].signal?.aborted).toBe(true);
 await resolve(1,22); await resolve(0,11);
 expect(screen.getByText('22 kg')).toBeTruthy(); expect(screen.queryByText('11 kg')).toBeNull();
});
it('does not let stale success clear loading while B is pending',async()=>{
 render(<App/>); await tick(); edit(); await tick(); await resolve(0,11);
 expect(screen.queryByText('11 kg')).toBeNull(); expect(screen.getByText('Syncing Telemetry...')).toBeTruthy();
 await resolve(1,22); expect(screen.queryByText('Syncing Telemetry...')).toBeNull();
});
it('debounces rapid input and cleans up StrictMode and unmount requests',async()=>{
 const view=render(<StrictMode><App/></StrictMode>); edit();
 fireEvent.change(screen.getAllByRole('spinbutton')[0],{target:{value:'30'}});
 await tick(); expect(requests).toHaveLength(1); view.unmount();
 expect(requests[0].signal?.aborted).toBe(true); await resolve(0,11);
 expect(view.container.textContent).toBe('');
});
it('ignores obsolete failures and recovers after a current failure',async()=>{
 const log=vi.spyOn(console,'error').mockImplementation(()=>{});
 render(<App/>); await tick(); edit(); await tick();
 await act(async()=>requests[0].reject(new Error('obsolete')));
 expect(log).not.toHaveBeenCalled(); expect(screen.getByText('Syncing Telemetry...')).toBeTruthy();
 await act(async()=>requests[1].reject(new Error('network')));
 expect(log).toHaveBeenCalledTimes(1); expect(screen.queryByText('Syncing Telemetry...')).toBeNull();
 fireEvent.change(screen.getAllByRole('spinbutton')[0],{target:{value:'30'}}); await tick(); await resolve(2,33);
 expect(screen.getByText('33 kg')).toBeTruthy();
});
