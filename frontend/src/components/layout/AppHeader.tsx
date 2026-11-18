import React from 'react';
import { Shield, PhoneCall, AlertTriangle } from 'lucide-react';

interface AppHeaderProps {
  environment?: string;
  isMock?: boolean;
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  environment = 'development',
  isMock = true,
}) => {
  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-sm">
      {/* Dev & Mock Notification Banner (Mandatory Rule 5 Compliance) */}
      {isMock && (
        <div className="bg-amber-500 text-slate-950 px-4 py-1 text-xs font-semibold text-center flex items-center justify-center gap-2">
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>DEV ENVIRONMENT: Integrations (SMS, Push, Maps, Payments) running in [MOCK] mode.</span>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-emergency-red flex items-center justify-center text-white shadow-md">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-xl tracking-tight text-slate-900">SafeHer</span>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
                {environment}
              </span>
            </div>
            <p className="text-xs text-slate-500 hidden sm:block">Privacy-First Women Safety Platform</p>
          </div>
        </div>

        {/* Immediate 112 Call-to-Action (Always visible) */}
        <div className="flex items-center gap-3">
          <a
            href="tel:112"
            className="flex items-center gap-2 bg-emergency-red hover:bg-emergency-red-dark text-white text-sm font-bold px-4 py-2 rounded-lg shadow-sm transition-colors focus:ring-4 focus:ring-emergency-red/20 active:scale-95"
            aria-label="Direct dial national emergency number 112"
          >
            <PhoneCall className="w-4 h-4 animate-bounce" />
            <span>Call 112</span>
          </a>
        </div>
      </div>
    </header>
  );
};
