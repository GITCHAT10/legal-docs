"use client";

import React, { useState, useEffect } from "react";

export default function AegisDashboard() {
  const [anomalies, setAnomalies] = useState([]);
  const [selectedAnomaly, setSelectedAnomaly] = useState(null);
  const [stats, setStats] = useState(null);
  const [view, setView] = useState("monitor"); // monitor | dashboard | logs | ops

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [anomRes, statsRes] = await Promise.all([
          fetch("http://localhost:8000/api/v1/anomalies"),
          fetch("http://localhost:8000/api/v1/dashboard/stats")
        ]);
        const anomData = await anomRes.json();
        const statsData = await statsRes.json();
        setAnomalies(anomData.data || []);
        setStats(statsData);
      } catch (e) {
        console.error(e);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const takeAction = async (id, action) => {
    if (!confirm(`Are you sure you want to ${action} this case?`)) return;
    try {
      await fetch(`http://localhost:8000/api/v1/anomalies/${id}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, notes: 'Action taken via ACI' })
      });
      setSelectedAnomaly(null);
    } catch (e) {
      alert('Action failed');
    }
  };

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 font-sans overflow-hidden">
      {/* Navigation */}
      <nav className="w-16 flex flex-col items-center py-6 bg-slate-900 border-r border-slate-800 gap-8">
        <div className="w-10 h-10 bg-blue-600 rounded flex items-center justify-center font-black text-white">A</div>
        <button onClick={() => setView('monitor')} title="Monitor" className={`p-2 rounded ${view === 'monitor' ? 'bg-blue-600/20 text-blue-400' : 'text-slate-500 hover:text-slate-300'}`}>
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2m0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
        </button>
        <button onClick={() => setView('dashboard')} title="Dashboard" className={`p-2 rounded ${view === 'dashboard' ? 'bg-blue-600/20 text-blue-400' : 'text-slate-500 hover:text-slate-300'}`}>
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z"></path></svg>
        </button>
        <button onClick={() => setView('ops')} title="Operations" className={`p-2 rounded ${view === 'ops' ? 'bg-blue-600/20 text-blue-400' : 'text-slate-500 hover:text-slate-300'}`}>
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
        </button>
        <button onClick={() => setView('logs')} title="Audit Trail" className={`p-2 rounded ${view === 'logs' ? 'bg-blue-600/20 text-blue-400' : 'text-slate-500 hover:text-slate-300'}`}>
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
        </button>
      </nav>

      {view === 'monitor' && (
        <>
          {/* Sidebar - Risk Monitor */}
          <div className="w-1/3 border-r border-slate-800 overflow-y-auto">
            <div className="p-4 border-b border-slate-800 bg-slate-900 sticky top-0 z-10">
              <h2 className="text-xl font-bold tracking-tighter uppercase">Live Risk Monitor</h2>
              <div className="flex gap-4 mt-2 text-[10px] font-mono uppercase tracking-widest">
                <span className="text-green-400">Stream: Active</span>
                <span className="text-slate-500">Node: AEGIS-01</span>
              </div>
            </div>
            <div className="divide-y divide-slate-900">
              {anomalies.map(a => (
                <div
                  key={a.id}
                  onClick={() => setSelectedAnomaly(a)}
                  className={`p-4 cursor-pointer transition-colors ${selectedAnomaly?.id === a.id ? 'bg-blue-900/30 border-l-4 border-blue-500' : 'hover:bg-slate-900 border-l-4 border-transparent'}`}
                >
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-[10px] font-mono text-slate-500 uppercase">{a.type}</span>
                    <span className={`text-xs font-bold px-1.5 rounded ${a.risk_score > 80 ? 'bg-red-900 text-red-400' : a.risk_score > 50 ? 'bg-yellow-900 text-yellow-400' : 'bg-green-900 text-green-400'}`}>{a.risk_score}</span>
                  </div>
                  <div className="font-bold text-sm">{a.aggregate_type} {a.aggregate_id}</div>
                  <div className="text-[10px] text-slate-500 mt-1 uppercase">{new Date(a.detected_at).toLocaleTimeString()}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Main Content - Case Investigation */}
          <div className="flex-1 flex flex-col overflow-hidden bg-slate-950/50">
            {selectedAnomaly ? (
              <>
                <div className="p-6 border-b border-slate-800 bg-slate-900/50 flex justify-between items-center">
                  <div>
                    <h1 className="text-2xl font-black uppercase tracking-tighter">Case #{selectedAnomaly.id.substring(0,8)}</h1>
                    <p className="text-slate-400 text-sm">Target: <span className="text-slate-200 font-mono">{selectedAnomaly.aggregate_type}/{selectedAnomaly.aggregate_id}</span></p>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => takeAction(selectedAnomaly.id, 'approve')} className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded text-xs font-black uppercase tracking-widest transition-all hover:scale-105 active:scale-95">APPROVE</button>
                    <button onClick={() => takeAction(selectedAnomaly.id, 'flag')} className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 rounded text-xs font-black uppercase tracking-widest transition-all hover:scale-105 active:scale-95">FLAG</button>
                    <button onClick={() => takeAction(selectedAnomaly.id, 'block')} className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded text-xs font-black uppercase tracking-widest transition-all hover:scale-105 active:scale-95">BLOCK</button>
                  </div>
                </div>

                <div className="flex-1 p-6 overflow-y-auto grid grid-cols-12 gap-6">
                  <div className="col-span-7 space-y-6">
                    <section className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
                      <h3 className="text-xs font-mono text-slate-500 uppercase mb-6 tracking-widest">Evidence Timeline</h3>
                      <div className="space-y-8 border-l-2 border-slate-800 ml-2 pl-8 relative">
                        <div className="relative">
                          <div className="absolute -left-[41px] top-1 w-6 h-6 rounded-full bg-slate-950 border-2 border-blue-500 flex items-center justify-center">
                            <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                          </div>
                          <div className="text-sm font-bold uppercase tracking-tight text-white">Event Captured</div>
                          <div className="text-xs text-slate-500 font-mono mt-1">{new Date(selectedAnomaly.detected_at).toISOString()}</div>
                        </div>
                        <div className="relative">
                          <div className="absolute -left-[41px] top-1 w-6 h-6 rounded-full bg-slate-950 border-2 border-red-500 flex items-center justify-center">
                            <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
                          </div>
                          <div className="text-sm font-bold uppercase tracking-tight text-red-400">Anomaly Detected</div>
                          <div className="text-xs text-slate-500 font-mono mt-1">{new Date(selectedAnomaly.detected_at).toISOString()}</div>
                        </div>
                      </div>
                    </section>

                    <section className="bg-gradient-to-br from-slate-900 to-slate-950 p-6 rounded-lg border border-slate-800 shadow-xl">
                      <div className="flex items-center gap-2 mb-4">
                        <div className="w-2 h-4 bg-blue-500"></div>
                        <h3 className="text-xs font-mono text-slate-500 uppercase tracking-widest">AI Explanation</h3>
                      </div>
                      <p className="text-sm leading-relaxed text-slate-300 italic">
                        "Mismatch detected in financial state for <span className="text-white font-bold">{selectedAnomaly.aggregate_id}</span>.
                        Rule: <span className="text-blue-400 font-mono">MIRA_COMPLIANCE_V2</span>.
                        Reason: Unexpected variance in tax/service charge ratio."
                      </p>
                    </section>
                  </div>

                  <div className="col-span-5 space-y-6">
                    <section className="bg-black/40 p-4 rounded-lg border border-slate-800">
                      <h3 className="text-[10px] font-mono text-slate-500 uppercase mb-3 tracking-widest">Data Diff</h3>
                      <pre className="text-[10px] font-mono text-blue-300 overflow-x-auto">{JSON.stringify(selectedAnomaly.diff, null, 2)}</pre>
                    </section>
                  </div>
                </div>
              </>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-600">
                <div className="w-12 h-12 border-2 border-slate-800 rounded-full mb-4 border-t-blue-500 animate-spin"></div>
                <div className="text-xs font-mono uppercase tracking-[0.2em]">Select Case</div>
              </div>
            )}
          </div>
        </>
      )}

      {view === 'dashboard' && (
        <div className="flex-1 p-10 overflow-y-auto">
          <h1 className="text-4xl font-black tracking-tighter uppercase mb-12 text-white">System Trust</h1>
          <div className="grid grid-cols-4 gap-6 mb-12">
            <div className="bg-slate-900 p-6 rounded border border-slate-800">
              <div className="text-[10px] font-mono text-slate-500 uppercase mb-2">Score</div>
              <div className="text-4xl font-black text-green-500">{stats?.trust_score}%</div>
            </div>
            <div className="bg-slate-900 p-6 rounded border border-slate-800">
              <div className="text-[10px] font-mono text-slate-500 uppercase mb-2">Monitored</div>
              <div className="text-4xl font-black text-white">{stats?.total_transactions}</div>
            </div>
          </div>
        </div>
      )}

      {view === 'ops' && (
        <div className="flex-1 p-10 overflow-y-auto">
          <header className="mb-12">
            <h1 className="text-4xl font-black tracking-tighter uppercase mb-2 text-white">Operational Execution</h1>
            <p className="text-slate-500 text-xs font-mono uppercase tracking-widest underline decoration-blue-500 decoration-2 underline-offset-4">SKYGODOWN Hub Control</p>
          </header>

          <div className="grid grid-cols-2 gap-8">
            <section className="bg-slate-900 p-6 rounded-lg border border-slate-800">
              <h3 className="text-xs font-mono text-blue-500 uppercase mb-6 tracking-[0.2em] font-black">Incoming Shipments</h3>
              <div className="space-y-4">
                {[1,2,3].map(i => (
                  <div key={i} className="flex justify-between items-center p-4 bg-slate-950 rounded border border-slate-800/50">
                    <div>
                      <div className="text-xs font-bold text-slate-100">SHIP-00{i}-MLE</div>
                      <div className="text-[10px] text-slate-500 uppercase font-mono">Consolidation: 84%</div>
                    </div>
                    <button className="px-3 py-1 bg-blue-600 rounded text-[10px] font-bold uppercase">DISPATCH</button>
                  </div>
                ))}
              </div>
            </section>

            <section className="bg-slate-900 p-6 rounded-lg border border-slate-800">
              <h3 className="text-xs font-mono text-green-500 uppercase mb-6 tracking-[0.2em] font-black">Air Capacity (ATOLLAIRWAYS)</h3>
              <div className="space-y-4">
                <div className="p-4 bg-slate-950 rounded border border-green-900/20">
                  <div className="flex justify-between mb-2">
                    <span className="text-[10px] font-mono text-slate-400">FLIGHT AW-102</span>
                    <span className="text-[10px] font-mono text-green-400">AVAILABLE</span>
                  </div>
                  <div className="text-sm font-bold text-white uppercase">DHC-6 Twin Otter (Cargo)</div>
                  <div className="mt-2 w-full h-1 bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-green-500" style={{width: '20%'}}></div>
                  </div>
                </div>
              </div>
            </section>
          </div>
        </div>
      )}

      {view === 'logs' && (
        <div className="flex-1 p-10 overflow-y-auto">
          <h1 className="text-3xl font-black uppercase mb-8 text-white">Audit Trail</h1>
          <div className="bg-slate-900 rounded border border-slate-800 overflow-hidden text-xs font-mono">
            <table className="w-full text-left">
              <thead className="bg-slate-800 text-slate-400 uppercase tracking-widest">
                <tr><th className="p-4">Time</th><th className="p-4">Type</th><th className="p-4">Integrity</th></tr>
              </thead>
              <tbody className="text-slate-300">
                {[...Array(5)].map((_, i) => (
                  <tr key={i} className="border-b border-slate-800"><td className="p-4">2026-04-16 18:00</td><td className="p-4">DECISION_MADE</td><td className="p-4 text-[10px] text-slate-600">verified_sha256</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
