import React, { useState } from 'react';
import { ShieldCheck, CheckCircle2, XCircle, Loader2 } from 'lucide-react';

interface ContactVerifyPageProps {
  token: string;
  onBack: () => void;
}

export const ContactVerifyPage: React.FC<ContactVerifyPageProps> = ({ token, onBack }) => {
  const [status, setStatus] = useState<'pending' | 'accepted' | 'declined'>('pending');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDecision = async (accept: boolean) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/contacts/verify/${token}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ accept }),
      });

      if (!res.ok) {
        throw new Error('This verification link is invalid or has already been used.');
      }

      setStatus(accept ? 'accepted' : 'declined');
    } catch (err: any) {
      setError(err.message || 'Error processing response');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto w-full px-4 py-12 space-y-6">
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden text-center">
        <div className="p-6 bg-gradient-to-b from-brand-50 to-white border-b border-slate-100">
          <div className="w-12 h-12 rounded-2xl bg-brand-600 text-white mx-auto flex items-center justify-center shadow-md mb-3">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">Emergency Contact Consent</h2>
          <p className="text-xs text-slate-500 mt-1">
            SafeHer operates on explicit consent. You have been nominated as an emergency contact.
          </p>
        </div>

        <div className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs">
              {error}
            </div>
          )}

          {status === 'pending' && (
            <div className="space-y-4">
              <p className="text-xs text-slate-600 text-left leading-relaxed">
                By accepting, you agree to receive SMS alerts with emergency location coordinates if this user triggers SOS or misses an automated journey check-in.
              </p>

              <div className="space-y-2.5 pt-2">
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => handleDecision(true)}
                  className="w-full py-2.5 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-xs font-bold shadow-sm transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-70"
                >
                  {loading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Accept & Confirm as Emergency Contact</span>
                    </>
                  )}
                </button>

                <button
                  type="button"
                  disabled={loading}
                  onClick={() => handleDecision(false)}
                  className="w-full py-2 border border-slate-200 hover:bg-slate-50 text-slate-600 rounded-xl text-xs font-semibold cursor-pointer"
                >
                  Decline Nomination
                </button>
              </div>
            </div>
          )}

          {status === 'accepted' && (
            <div className="py-6 space-y-2 animate-in zoom-in">
              <CheckCircle2 className="w-12 h-12 text-emerald-600 mx-auto" />
              <h4 className="font-bold text-slate-900 text-base">You Are Now a Verified Contact</h4>
              <p className="text-xs text-slate-500">
                You will be notified immediately if your contact triggers an emergency SOS.
              </p>
            </div>
          )}

          {status === 'declined' && (
            <div className="py-6 space-y-2 animate-in zoom-in">
              <XCircle className="w-12 h-12 text-slate-400 mx-auto" />
              <h4 className="font-bold text-slate-800 text-base">Nomination Declined</h4>
              <p className="text-xs text-slate-500">
                You will not receive any emergency alerts or coordinates from this account.
              </p>
            </div>
          )}

          <div className="pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={onBack}
              className="text-xs text-brand-600 hover:underline"
            >
              Back to Home
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
