import React from 'react';
import { Shield, ShieldAlert, ShieldCheck } from 'lucide-react';

interface HardwareGuardianProps {
  isBound: boolean;
  trustScore: number;
}

export const HardwareGuardian: React.FC<HardwareGuardianProps> = ({ isBound, trustScore }) => {
  const isSecure = isBound && trustScore >= 0.90;

  return (
    <div className={`p-4 rounded-lg border ${isSecure ? 'bg-green-900/20 border-green-500' : 'bg-red-900/20 border-red-500'}`}>
      <div className="flex items-center space-x-3">
        {isSecure ? (
          <ShieldCheck className="text-green-500 w-8 h-8" />
        ) : (
          <ShieldAlert className="text-red-500 w-8 h-8" />
        )}
        <div>
          <h3 className="text-lg font-mono text-white">AEGIS Guardian</h3>
          <p className="text-sm text-gray-400 font-mono">
            {isBound ? 'Bound' : 'UNBOUND'} | Trust: {(trustScore * 100).toFixed(2)}%
          </p>
        </div>
      </div>
      {!isSecure && (
        <div className="mt-4 p-2 bg-red-600 text-white text-xs font-bold text-center uppercase animate-pulse">
          Sovereign Signature Violation: System Locked
        </div>
      )}
    </div>
  );
};
