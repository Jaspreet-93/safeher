import React from 'react';
import { Shield, PhoneCall, AlertTriangle, User, Home, LogIn } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

interface AppHeaderProps {
  environment?: string;
  isMock?: boolean;
  currentView: 'home' | 'auth' | 'profile';
  onNavigate: (view: 'home' | 'auth' | 'profile') => void;
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  environment = 'development',
  isMock = true,
  currentView,
  onNavigate,
}) => {
  const { user, isAuthenticated } = useAuth();

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
        <div
          onClick={() => onNavigate('home')}
          className="flex items-center gap-3 cursor-pointer"
        >
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

        {/* Navigation & Actions */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => onNavigate('home')}
            className={`p-2 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
              currentView === 'home'
                ? 'bg-slate-100 text-slate-900'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <Home className="w-4 h-4" />
            <span className="hidden sm:inline">Home</span>
          </button>

          {isAuthenticated ? (
            <button
              type="button"
              onClick={() => onNavigate('profile')}
              className={`p-2 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                currentView === 'profile'
                  ? 'bg-slate-100 text-slate-900'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <User className="w-4 h-4 text-brand-600" />
              <span className="hidden sm:inline">{user?.email?.split('@')[0]}</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={() => onNavigate('auth')}
              className={`p-2 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                currentView === 'auth'
                  ? 'bg-brand-50 text-brand-700'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <LogIn className="w-4 h-4 text-brand-600" />
              <span className="hidden sm:inline">Sign In / Register</span>
            </button>
          )}

          {/* Immediate 112 Call-to-Action (Always visible) */}
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
