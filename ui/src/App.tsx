import React, { useState, useEffect } from 'react';
import { Shield, Lock, AlertTriangle, Menu, Map as MapIcon, Activity, Clock, LogOut } from 'lucide-react';

const WarRoomUI = () => {
  const [alertLevel, setAlertLevel] = useState('Normal');
  const [events, setEvents] = useState([
    { id: 'EVT-001', zone: 'Perimeter A', type: 'Person', confidence: 0.92, time: '12:00:01', hash: '8a2f...' },
    { id: 'EVT-002', zone: 'Sala_Fushi_Dock', type: 'Boat', confidence: 0.88, time: '12:05:15', hash: '3c1d...', mfr_score: '2/3' }
  ]);

  const [syncStatus, setSyncStatus] = useState('LOCAL_AUTONOMOUS');

  return (
    <div className="flex flex-col h-screen bg-slate-900 text-slate-100 font-mono">
      {/* Top Bar */}
      <header className="flex items-center justify-between px-6 py-3 bg-slate-800 border-b border-slate-700">
        <div className="flex items-center gap-4">
          <Shield className="text-blue-400 w-8 h-8" />
          <h1 className="text-xl font-bold">MNOS COMMAND CENTER [SALA FUSHI]</h1>
        </div>
        <div className="flex items-center gap-8">
          <div className="flex flex-col items-end">
            <span className="text-xs text-slate-400 uppercase tracking-widest">Alert Level</span>
            <span className={`text-lg font-bold ${alertLevel === 'Secure' ? 'text-red-500' : 'text-green-500'}`}>{alertLevel}</span>
          </div>
          <div className="flex flex-col items-end border-l border-slate-700 pl-8">
            <span className="text-xs text-slate-400 uppercase tracking-widest">Cognitive Isolation</span>
            <span className="text-lg font-bold text-cyan-400 italic">{syncStatus}</span>
          </div>
          <div className="flex flex-col items-end border-l border-slate-700 pl-8">
            <span className="text-xs text-slate-400 uppercase tracking-widest">SHADOW Ledger</span>
            <span className="text-lg font-bold text-blue-400 italic">HEALTHY</span>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Nav */}
        <aside className="w-16 bg-slate-800 border-r border-slate-700 flex flex-col items-center py-6 gap-8">
          <MapIcon className="text-slate-400 hover:text-white cursor-pointer" />
          <Activity className="text-slate-400 hover:text-white cursor-pointer" />
          <Clock className="text-slate-400 hover:text-white cursor-pointer" />
        </aside>

        {/* Center: Map & Streams */}
        <main className="flex-1 bg-slate-950 p-6 flex flex-col gap-6 overflow-auto">
          <div className="flex-1 bg-slate-900 border border-slate-800 rounded-lg relative flex items-center justify-center text-slate-700">
             [3D MAP OVERLAY: SALA FUSHI PERIMETER]
             <div className="absolute top-4 left-4 bg-slate-800/80 p-2 rounded text-xs text-slate-300">
               Nodes Online: 12/12
             </div>
          </div>

          <div className="h-64 grid grid-cols-3 gap-4">
            <div className="bg-black rounded border border-slate-800 flex items-center justify-center text-xs text-slate-500">LIVE: MAIN GATE</div>
            <div className="bg-black rounded border border-slate-800 flex items-center justify-center text-xs text-slate-500">LIVE: NORTH BEACH</div>
            <div className="bg-black rounded border border-slate-800 flex items-center justify-center text-xs text-slate-500">LIVE: STAFF QUARTERS</div>
          </div>
        </main>

        {/* Right Panel: Actions */}
        <aside className="w-80 bg-slate-800 border-l border-slate-700 p-6 flex flex-col gap-8">
          <div>
            <h3 className="text-xs text-slate-400 uppercase tracking-widest mb-4">Active Alerts</h3>
            <div className="space-y-4">
              {events.map(e => (
                <div key={e.id} className="bg-slate-900 p-3 rounded border-l-4 border-amber-500">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-amber-400 font-bold">{e.id}</span>
                    <span className="text-slate-500">{e.time}</span>
                  </div>
                  <div className="text-sm">{e.type} detected in {e.zone}</div>
                  {e.mfr_score && (
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] text-slate-400 uppercase">MFR:</span>
                      <span className={`text-xs font-bold ${e.mfr_score === '3/3' ? 'text-green-500' : 'text-red-500'}`}>{e.mfr_score}</span>
                    </div>
                  )}
                  <div className="text-[10px] text-slate-600 mt-2 truncate">Hash: {e.hash}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-auto space-y-3">
            <h3 className="text-xs text-slate-400 uppercase tracking-widest mb-4">AEGIS Safe Actions</h3>
            <button
              className="w-full py-3 bg-red-900/30 border border-red-900 text-red-500 rounded hover:bg-red-900/50 flex items-center justify-center gap-2"
              onClick={() => setAlertLevel('Secure')}
            >
              <Lock size={16} /> RESTRICT ENTRY (TL-3)
            </button>
            <button className="w-full py-3 bg-slate-700 text-slate-300 rounded hover:bg-slate-600 flex items-center justify-center gap-2">
               ACKNOWLEDGE ALL
            </button>

            <div className="pt-4 border-t border-slate-700 mt-4">
               <button className="w-full py-4 bg-green-900/20 border border-green-800 text-green-500 rounded flex items-center justify-center gap-2 font-bold uppercase tracking-widest">
                 <LogOut size={18} /> Emergency Egress
               </button>
               <p className="text-[10px] text-slate-500 mt-2 text-center">SAFETY INVARIANT: Mechanical exit always available.</p>
            </div>
          </div>
        </aside>
      </div>

      {/* Bottom Panel: SHADOW Audit */}
      <footer className="h-48 bg-slate-900 border-t border-slate-700 p-4 font-mono text-[11px] overflow-auto">
        <h3 className="text-xs text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-2">
          <Activity size={12} /> SHADOW Forensic Ledger (Live)
        </h3>
        <div className="space-y-1">
          <div className="text-slate-500">[2026-04-22T12:00:01Z] EVENT_TYPE: nexus.guest.arrival | HASH: 0523eb... | PREV: 000000... | STATUS: COMMITTED</div>
          <div className="text-slate-500">[2026-04-22T12:05:15Z] EVENT_TYPE: nexus.security.alert | HASH: 3c1d92... | PREV: 0523eb... | STATUS: COMMITTED | MFR_FAIL: JETTY-B</div>
          <div className="text-red-400">[2026-04-22T12:05:16Z] EVENT_TYPE: nexus.security.kinetic_defense | KINETIC_LOCK: FUEL_PUMPS_OFF | HMS_LOCKED</div>
          <div className="text-blue-400">[LIVE] --- WAITING FOR NEXT SOVEREIGN HANDSHAKE ---</div>
        </div>
      </footer>
    </div>
  );
};

export default WarRoomUI;
