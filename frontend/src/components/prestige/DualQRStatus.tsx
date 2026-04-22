import React from 'react';
import { QrCode, ArrowRight, CheckCircle2 } from 'lucide-react';

interface DualQRStatusProps {
  fleetStatus: 'PENDING' | 'SUCCESS';
  ledgerStatus: 'PENDING' | 'SUCCESS';
}

export const DualQRStatus: React.FC<DualQRStatusProps> = ({ fleetStatus, ledgerStatus }) => {
  const isComplete = fleetStatus === 'SUCCESS' && ledgerStatus === 'SUCCESS';

  return (
    <div className="p-4 bg-slate-900 rounded-lg border border-slate-700">
      <div className="flex items-center justify-between">
        <div className="flex flex-col items-center">
          <QrCode className={`${fleetStatus === 'SUCCESS' ? 'text-green-500' : 'text-slate-500'} w-10 h-10`} />
          <span className="text-[10px] mt-1 font-mono text-slate-400">FLEET</span>
        </div>

        <ArrowRight className={`${isComplete ? 'text-green-500' : 'text-slate-700'} w-6 h-6 animate-pulse`} />

        <div className="flex flex-col items-center">
          <CheckCircle2 className={`${ledgerStatus === 'SUCCESS' ? 'text-green-500' : 'text-slate-500'} w-10 h-10`} />
          <span className="text-[10px] mt-1 font-mono text-slate-400">LEDGER</span>
        </div>
      </div>

      {isComplete && (
        <div className="mt-3 text-center text-xs font-bold text-green-500 uppercase tracking-widest font-mono">
          Handshake Verified
        </div>
      )}
    </div>
  );
};
