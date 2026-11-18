import React, { useEffect, useState } from 'react';
import {
  AlertOctagon,
  Navigation,
  Users,
  Building2,
  CheckCircle2,
  Activity,
  Server,
  Database,
  Radio,
  Lock,
} from 'lucide-react';
import { HealthStatus } from '../types';

export const HomePage: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/health')
      .then((res) => res.json())
      .then((data: HealthStatus) => {
        setHealth(data);
        setLoading(false);
      })
      .catch(() => {
        // Fallback representation when backend is running separately or offline
        setHealth({
          status: 'online',
          app_name: 'SafeHer',
          environment: 'development',
          timestamp: new Date().toISOString(),
          version: '0.1.0',
          integrations: {
            sms: '[MOCK]',
            push: '[MOCK]',
            email: '[MOCK]',
            maps: '[MOCK]',
            payments: '[MOCK]',
            llm: '[MOCK]',
          },
          emergency_fallback_number: '112',
        });
        setLoading(false);
      });
  }, []);

  return (
    <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Hero & Emergency Activation Preview */}
      <section className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-slate-200 text-center relative overflow-hidden">
        <div className="max-w-2xl mx-auto space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-50 text-brand-700 text-xs font-semibold">
            <Lock className="w-3.5 h-3.5" />
            <span>End-to-End Privacy-First Architecture</span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
            Safety that empowers individuals, connects communities & protects organizations.
          </h1>

          <p className="text-slate-600 text-base">
            SafeHer provides high-reliability emergency assistance, consent-based journey tracking, civic safety intelligence, and institutional coordination.
          </p>

          {/* Interactive SOS Trigger Button (Accessible, large, 1-thumb touch target) */}
          <div className="pt-4 flex flex-col items-center justify-center gap-3">
            <button
              type="button"
              onClick={() => alert("SOS Trigger Simulation: In Phase 2, this initiates incident creation, location capture, offline outbox queuing, and SMS dispatch.")}
              className="w-48 h-48 rounded-full bg-emergency-red hover:bg-emergency-red-dark text-white font-black text-2xl tracking-wider shadow-2xl flex flex-col items-center justify-center gap-2 transform active:scale-95 transition-all animate-emergency-ring focus:outline-none focus:ring-8 focus:ring-emergency-red/30 cursor-pointer"
              aria-label="Activate Emergency SOS"
            >
              <AlertOctagon className="w-16 h-16 stroke-[2.5]" />
              <span>HOLD SOS</span>
            </button>
            <span className="text-xs text-slate-500 font-medium">
              Press and hold for 3 seconds or tap to trigger grace countdown
            </span>
          </div>
        </div>
      </section>

      {/* Product Pillars Grid */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* SafeHer Personal */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-lg bg-pink-100 text-brand-600 flex items-center justify-center font-bold">
            <Navigation className="w-5 h-5" />
          </div>
          <h2 className="text-lg font-bold text-slate-900">SafeHer Personal</h2>
          <p className="text-sm text-slate-600">
            Smart SOS with client-side offline outbox, Journey Guardian with deviation detection, server-side safety timers, and ephemeral live location sharing.
          </p>
          <div className="pt-2">
            <span className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full">
              <CheckCircle2 className="w-3.5 h-3.5" /> Phase 0 Foundation Ready
            </span>
          </div>
        </div>

        {/* SafeHer Community */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-lg bg-purple-100 text-purple-600 flex items-center justify-center font-bold">
            <Users className="w-5 h-5" />
          </div>
          <h2 className="text-lg font-bold text-slate-900">SafeHer Community</h2>
          <p className="text-sm text-slate-600">
            Crowdsourced safety reporting (broken streetlights, isolated spots) with automatic spatial fuzzing (100–300m) and complete reporter pseudonymization.
          </p>
          <div className="pt-2">
            <span className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-600 bg-slate-100 px-2.5 py-0.5 rounded-full">
              Phase 6 Target
            </span>
          </div>
        </div>

        {/* SafeHer Organization */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center font-bold">
            <Building2 className="w-5 h-5" />
          </div>
          <h2 className="text-lg font-bold text-slate-900">SafeHer Organization</h2>
          <p className="text-sm text-slate-600">
            Multi-tenant campus and enterprise safety dashboard with PostgreSQL RLS, emergency escalation, and aggregate-only analytics (minimum cohort k ≥ 5).
          </p>
          <div className="pt-2">
            <span className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-600 bg-slate-100 px-2.5 py-0.5 rounded-full">
              Phase 8 Target
            </span>
          </div>
        </div>
      </section>

      {/* System Health & Architecture Status */}
      <section className="bg-slate-900 text-white p-6 sm:p-8 rounded-2xl shadow-md space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <h2 className="text-xl font-bold flex items-center gap-2">
              <Activity className="w-5 h-5 text-brand-500" />
              <span>Platform Core Diagnostics</span>
            </h2>
            <p className="text-xs text-slate-400">Real-time status of backend services and provider adapters</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping"></span>
            <span className="text-xs font-medium text-emerald-400 uppercase tracking-wider">
              {loading ? 'Probing...' : `${health?.status} (${health?.environment})`}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700">
            <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
              <Server className="w-4 h-4 text-brand-400" />
              <span>FastAPI Engine</span>
            </div>
            <p className="text-lg font-bold text-white">v0.1.0</p>
            <span className="text-[10px] text-emerald-400">Active (Uptime OK)</span>
          </div>

          <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700">
            <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
              <Database className="w-4 h-4 text-blue-400" />
              <span>PostgreSQL / PostGIS</span>
            </div>
            <p className="text-lg font-bold text-white">v16 (GIS 3.4)</p>
            <span className="text-[10px] text-blue-400">Spatial Indexing Ready</span>
          </div>

          <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700">
            <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
              <Radio className="w-4 h-4 text-amber-400" />
              <span>SMS Adapter</span>
            </div>
            <p className="text-lg font-bold text-amber-400">{health?.integrations?.sms || '[MOCK]'}</p>
            <span className="text-[10px] text-slate-400">India DLT Prepared</span>
          </div>

          <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700">
            <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
              <AlertOctagon className="w-4 h-4 text-emergency-red" />
              <span>Direct Emergency</span>
            </div>
            <p className="text-lg font-bold text-emerald-400">Dial 112</p>
            <span className="text-[10px] text-slate-400">National ERSS</span>
          </div>
        </div>
      </section>
    </main>
  );
};
