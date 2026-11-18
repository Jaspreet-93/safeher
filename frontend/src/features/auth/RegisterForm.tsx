import React, { useState } from 'react';
import { Mail, Lock, User, Phone, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { ConsentNoticeModal } from './ConsentNoticeModal';

interface RegisterFormProps {
  onSuccess: () => void;
  onSwitchToLogin: () => void;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({ onSuccess, onSwitchToLogin }) => {
  const { register } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [termsConsent, setTermsConsent] = useState(false);
  const [locationConsent, setLocationConsent] = useState(true);
  const [showConsentModal, setShowConsentModal] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Simple password strength calculator
  const calculateStrength = (pwd: string): { label: string; score: number; color: string } => {
    let score = 0;
    if (pwd.length >= 8) score++;
    if (/[A-Z]/.test(pwd)) score++;
    if (/[0-9]/.test(pwd)) score++;
    if (/[^A-Za-z0-9]/.test(pwd)) score++;

    if (score <= 1) return { label: 'Weak', score: 25, color: 'bg-red-500' };
    if (score === 2) return { label: 'Fair', score: 50, color: 'bg-amber-500' };
    if (score === 3) return { label: 'Good', score: 75, color: 'bg-blue-500' };
    return { label: 'Strong (Argon2id Ready)', score: 100, color: 'bg-emerald-500' };
  };

  const strength = calculateStrength(password);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!termsConsent) {
      setError('You must accept the Terms of Service & Privacy Notice under DPDPA 2023 to register.');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      await register({
        full_name: fullName,
        email,
        password,
        phone_number: phoneNumber || null,
        terms_consent: termsConsent,
        location_consent: locationConsent,
      });
      onSuccess();
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs flex items-start gap-2 animate-in fade-in">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Full Name
          </label>
          <div className="relative">
            <User className="w-5 h-5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Priya Sharma"
              className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 transition-all"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Email Address
          </label>
          <div className="relative">
            <Mail className="w-5 h-5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="priya@domain.com"
              className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 transition-all"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Mobile Number (Optional)
          </label>
          <div className="relative">
            <Phone className="w-5 h-5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="tel"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              placeholder="+91 98765 43210"
              className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 transition-all"
            />
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Password
            </label>
            {password && (
              <span className="text-[10px] font-semibold text-slate-500">
                {strength.label}
              </span>
            )}
          </div>
          <div className="relative">
            <Lock className="w-5 h-5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Minimum 8 characters"
              className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 transition-all"
            />
          </div>
          {password && (
            <div className="mt-1.5 h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
              <div
                className={`h-full ${strength.color} transition-all duration-300`}
                style={{ width: `${strength.score}%` }}
              />
            </div>
          )}
        </div>

        {/* DPDPA 2023 Explicit Consent Items */}
        <div className="space-y-2.5 pt-2 border-t border-slate-100">
          <label className="flex items-start gap-2.5 cursor-pointer">
            <input
              type="checkbox"
              required
              checked={termsConsent}
              onChange={(e) => setTermsConsent(e.target.checked)}
              className="mt-1 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
            />
            <span className="text-xs text-slate-600 leading-tight">
              I agree to the{' '}
              <button
                type="button"
                onClick={() => setShowConsentModal(true)}
                className="text-brand-600 underline font-medium hover:text-brand-700"
              >
                Terms of Service & Privacy Notice
              </button>{' '}
              under India's DPDPA 2023. <strong className="text-red-500">*Required</strong>
            </span>
          </label>

          <label className="flex items-start gap-2.5 cursor-pointer">
            <input
              type="checkbox"
              checked={locationConsent}
              onChange={(e) => setLocationConsent(e.target.checked)}
              className="mt-1 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
            />
            <span className="text-xs text-slate-600 leading-tight">
              I grant permission to process my device location during active SOS alerts and journeys (Revocable anytime).
            </span>
          </label>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-sm font-semibold shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-70 cursor-pointer"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Creating Secure Account...</span>
            </>
          ) : (
            <span>Create Account with Privacy Consent</span>
          )}
        </button>

        <div className="text-center pt-1">
          <button
            type="button"
            onClick={onSwitchToLogin}
            className="text-xs text-brand-600 hover:text-brand-700 font-medium"
          >
            Already have an account? Sign in
          </button>
        </div>
      </form>

      <ConsentNoticeModal isOpen={showConsentModal} onClose={() => setShowConsentModal(false)} />
    </>
  );
};
