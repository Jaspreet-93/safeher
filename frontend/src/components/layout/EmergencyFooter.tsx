import React from 'react';
import { ShieldAlert, HeartHandshake, EyeOff, Radio } from 'lucide-react';

export const EmergencyFooter: React.FC = () => {
  return (
    <footer className="mt-auto bg-slate-900 text-slate-400 text-xs py-8 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-white font-semibold">
              <ShieldAlert className="w-4 h-4 text-brand-500" />
              <span>Emergency 112</span>
            </div>
            <p className="text-slate-400">
              India National Emergency Response Support System (ERSS). Available 24/7 toll-free from all mobile networks.
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-white font-semibold">
              <EyeOff className="w-4 h-4 text-emerald-400" />
              <span>Zero Monetization</span>
            </div>
            <p className="text-slate-400">
              SafeHer strictly never sells, monetizes, or shares emergency telemetry or live location coordinates for advertising.
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-white font-semibold">
              <HeartHandshake className="w-4 h-4 text-blue-400" />
              <span>Consent-First</span>
            </div>
            <p className="text-slate-400">
              Nobody sees your location without explicit, revocable, and time-limited authorization. Organizations never track in secret.
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-white font-semibold">
              <Radio className="w-4 h-4 text-amber-400" />
              <span>Fail Loudly</span>
            </div>
            <p className="text-slate-400">
              If an emergency alert fails to reach telecom gateways, SafeHer immediately notifies you with native phone and SMS fallback options.
            </p>
          </div>
        </div>

        <div className="pt-6 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© {new Date().getFullYear()} SafeHer Platform. Built for real-world reliability and human privacy.</p>
          <div className="flex gap-4">
            <a href="#privacy" className="hover:text-white transition-colors">Privacy Notice</a>
            <a href="#terms" className="hover:text-white transition-colors">Terms of Assistance</a>
            <a href="#limits" className="hover:text-white transition-colors">Operating Limits</a>
          </div>
        </div>
      </div>
    </footer>
  );
};
