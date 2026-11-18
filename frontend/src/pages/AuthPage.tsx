import React, { useState } from 'react';
import { Shield, Lock, EyeOff, CheckCircle2 } from 'lucide-react';
import { LoginForm } from '../features/auth/LoginForm';
import { RegisterForm } from '../features/auth/RegisterForm';

interface AuthPageProps {
  onSuccess: () => void;
}

export const AuthPage: React.FC<AuthPageProps> = ({ onSuccess }) => {
  const [mode, setMode] = useState<'login' | 'register'>('login');

  return (
    <div className="max-w-md mx-auto w-full px-4 py-8">
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        {/* Header Branding */}
        <div className="p-6 bg-gradient-to-b from-brand-50/60 to-white text-center border-b border-slate-100">
          <div className="w-12 h-12 rounded-2xl bg-brand-600 text-white mx-auto flex items-center justify-center shadow-md mb-3">
            <Shield className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">
            {mode === 'login' ? 'Welcome Back to SafeHer' : 'Create Your SafeHer Account'}
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            {mode === 'login'
              ? 'Enter your credentials to manage contacts, journeys, and alerts'
              : 'End-to-end privacy-first safety with DPDPA 2023 consent protection'}
          </p>

          {/* Tab Switcher */}
          <div className="flex bg-slate-100 p-1 rounded-xl mt-4 max-w-xs mx-auto">
            <button
              type="button"
              onClick={() => setMode('login')}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                mode === 'login'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => setMode('register')}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                mode === 'register'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Register
            </button>
          </div>
        </div>

        {/* Form Container */}
        <div className="p-6">
          {mode === 'login' ? (
            <LoginForm onSuccess={onSuccess} onSwitchToRegister={() => setMode('register')} />
          ) : (
            <RegisterForm onSuccess={onSuccess} onSwitchToLogin={() => setMode('login')} />
          )}
        </div>

        {/* Security & Privacy Footer Notes */}
        <div className="p-4 bg-slate-50 border-t border-slate-100 text-[11px] text-slate-500 flex items-center justify-around">
          <div className="flex items-center gap-1">
            <Lock className="w-3.5 h-3.5 text-slate-400" />
            <span>Argon2id Hashes</span>
          </div>
          <div className="flex items-center gap-1">
            <EyeOff className="w-3.5 h-3.5 text-slate-400" />
            <span>Zero Monetization</span>
          </div>
          <div className="flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
            <span>DPDPA 2023</span>
          </div>
        </div>
      </div>
    </div>
  );
};
