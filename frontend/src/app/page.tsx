"use client";

import React, { useState, useEffect } from "react";

export default function AegisDashboard() {
  const [anomalies, setAnomalies] = useState([]);
  const [selectedAnomaly, setSelectedAnomaly] = useState(null);
  const [stats, setStats] = useState(null);
  const [view, setView] = useState("monitor"); // monitor | dashboard

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
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
        </button>
        <button onClick={() => setView('dashboard')} title="Dashboard" className={`p-2 rounded ${view === 'dashboard' ? 'bg-blue-600/20 text-blue-400' : 'text-slate-500 hover:text-slate-300'}`}>
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z"></path></svg>
        </button>
      </nav>

      {view === 'monitor' ? (
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
                          <div className="text-sm font-bold uppercase tracking-tight">Event Captured</div>
                          <div className="text-xs text-slate-500 font-mono mt-1">{new Date(selectedAnomaly.detected_at).toISOString()}</div>
                          <div className="mt-2 text-xs text-slate-400 bg-slate-950 p-3 rounded font-mono border border-slate-800/50">
                            SOURCE: {selectedAnomaly.aggregate_type}<br/>
                            ID: {selectedAnomaly.aggregate_id}
                          </div>
                        </div>
                        <div className="relative">
                          <div className="absolute -left-[41px] top-1 w-6 h-6 rounded-full bg-slate-950 border-2 border-red-500 flex items-center justify-center">
                            <div className="w-2 h-2 rounded-full bg-red-500 animate-ping"></div>
                          </div>
                          <div className="text-sm font-bold uppercase tracking-tight text-red-400">Anomaly Detected</div>
                          <div className="text-xs text-slate-500 font-mono mt-1">{new Date(selectedAnomaly.detected_at).toISOString()}</div>
                          <div className="mt-2 text-xs text-red-100 bg-red-950/20 p-3 rounded font-mono border border-red-900/30">
                            TYPE: {selectedAnomaly.type}<br/>
                            DETECTOR: {selectedAnomaly.detector_class?.split('\\').pop()}<br/>
                            RISK SCORE: {selectedAnomaly.risk_score}
                          </div>
                        </div>
                      </div>
                    </section>

                    <section className="bg-gradient-to-br from-slate-900 to-slate-950 p-6 rounded-lg border border-slate-800 shadow-xl">
                      <div className="flex items-center gap-2 mb-4">
                        <div className="w-2 h-4 bg-blue-500"></div>
                        <h3 className="text-xs font-mono text-slate-500 uppercase tracking-widest">AI Explanation</h3>
                      </div>
                      <p className="text-sm leading-relaxed text-slate-300">
                        This transaction on <span className="text-blue-400 font-bold underline font-mono">{selectedAnomaly.aggregate_id}</span> was flagged by the <span className="text-white font-bold">{selectedAnomaly.detector_class?.split('\\').pop()}</span> module.
                        A mismatch was detected in the <span className="text-red-400 font-bold">financial state</span> which deviates from the expected MIRA-compliant operating rules.
                        System recommends <span className="text-yellow-400 font-bold italic">FLAGGING</span> for manual oversight due to possible value shaving or tax calculation variance.
                      </p>
                    </section>
                  </div>

                  <div className="col-span-5 space-y-6">
                    <section className="bg-black/40 p-4 rounded-lg border border-slate-800">
                      <h3 className="text-[10px] font-mono text-slate-500 uppercase mb-3 tracking-widest">Data State Diff</h3>
                      <div className="font-mono text-[11px] text-blue-300">
                        <pre className="whitespace-pre-wrap">{JSON.stringify(selectedAnomaly.diff, null, 2)}</pre>
                      </div>
                    </section>

                    <section className="bg-slate-900/30 p-4 rounded-lg border border-slate-800">
                      <h3 className="text-[10px] font-mono text-slate-500 uppercase mb-4 tracking-widest">Risk Analysis Breakdown</h3>
                      <div className="space-y-3">
                        {Object.entries(selectedAnomaly.scoring_breakdown || {}).map(([key, val]) => (
                          <div key={key} className="space-y-1">
                            <div className="flex justify-between items-end">
                              <span className="text-[10px] uppercase text-slate-500 font-bold">{key}</span>
                              <span className="text-sm font-black text-white">{val.score}<span className="text-[10px] text-slate-600 ml-1">/100</span></span>
                            </div>
                            <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
                              <div className="h-full bg-blue-600" style={{width: `${val.score}%`}}></div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </section>

                    <section className="bg-blue-600/5 p-4 rounded-lg border border-blue-900/30">
                      <h3 className="text-[10px] font-mono text-blue-500 uppercase mb-2 tracking-widest">Origin Trace</h3>
                      <div className="text-[10px] font-mono text-slate-400 space-y-1">
                        <div>SOURCE SYSTEM: BUBBLE_GATEWAY_01</div>
                        <div>NODE: MV-MLE-DC1</div>
                        <div>IDEMPOTENCY: {selectedAnomaly.source_event_id?.substring(0,12)}...</div>
                      </div>
                    </section>
                  </div>
                </div>
              </>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-600 animate-pulse">
                <div className="w-12 h-12 border-2 border-slate-800 rounded-full mb-4 border-t-blue-500 animate-spin"></div>
                <div className="text-xs font-mono uppercase tracking-[0.2em]">Awaiting Case Selection</div>
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="flex-1 p-10 overflow-y-auto">
          <header className="mb-12">
            <h1 className="text-4xl font-black tracking-tighter uppercase mb-2 text-white">System Trust Dashboard</h1>
            <div className="h-1 w-20 bg-blue-600"></div>
          </header>

          <div className="grid grid-cols-4 gap-6 mb-12">
            <div className="bg-slate-900 p-6 rounded-lg border border-slate-800">
              <div className="text-[10px] font-mono text-slate-500 uppercase mb-2">Global Trust Score</div>
              <div className="text-5xl font-black text-green-500">{stats?.trust_score}%</div>
              <div className="text-[10px] text-slate-400 mt-2">↑ 0.4% from last 24h</div>
            </div>
            <div className="bg-slate-900 p-6 rounded-lg border border-slate-800">
              <div className="text-[10px] font-mono text-slate-500 uppercase mb-2">Monitored Transactions</div>
              <div className="text-5xl font-black text-white">{stats?.total_transactions}</div>
              <div className="text-[10px] text-slate-400 mt-2">Across 5 ecosystem modules</div>
            </div>
            <div className="bg-slate-900 p-6 rounded-lg border border-slate-800">
              <div className="text-[10px] font-mono text-slate-500 uppercase mb-2">Active Anomalies</div>
              <div className="text-5xl font-black text-red-500">{stats?.flagged_anomalies}</div>
              <div className="text-[10px] text-slate-400 mt-2">Requires immediate triage</div>
            </div>
            <div className="bg-slate-900 p-6 rounded-lg border border-slate-800">
              <div className="text-[10px] font-mono text-slate-500 uppercase mb-2">Resolution Rate</div>
              <div className="text-5xl font-black text-blue-500">84%</div>
              <div className="text-[10px] text-slate-400 mt-2">Average time to resolve: 12m</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-8">
            <section className="bg-slate-900 p-6 rounded-lg border border-slate-800">
              <h3 className="text-sm font-bold uppercase mb-6 tracking-widest text-slate-400">Anomaly Trends (Last 7 Days)</h3>
              <div className="flex items-end gap-2 h-48">
                {stats?.trends.map(t => (
                  <div key={t.date} className="flex-1 flex flex-col items-center gap-2">
                    <div className="w-full bg-blue-600/20 hover:bg-blue-600 transition-colors rounded-t" style={{height: `${t.count * 10}px`}}></div>
                    <div className="text-[8px] font-mono text-slate-600 rotate-45 mt-2">{t.date.split('-').slice(1).join('/')}</div>
                  </div>
                ))}
              </div>
            </section>

            <section className="bg-slate-900 p-6 rounded-lg border border-slate-800">
              <h3 className="text-sm font-bold uppercase mb-6 tracking-widest text-slate-400">Risk by Ecosystem Module</h3>
              <div className="space-y-4">
                {stats && Object.entries(stats.module_risk).map(([module, score]) => (
                  <div key={module} className="flex items-center gap-4">
                    <div className="w-24 text-[10px] font-mono text-slate-400 font-bold">{module}</div>
                    <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]" style={{width: `${score}%`}}></div>
                    </div>
                    <div className="w-8 text-right text-[10px] font-mono font-bold">{score}%</div>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </div>
      )}
    </div>
  );
}
