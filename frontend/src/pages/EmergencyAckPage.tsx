import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  PhoneCall,
  MapPin,
  ExternalLink,
  Shield,
  Clock,
  Loader2,
} from 'lucide-react';

interface EmergencyAckPageProps {
  token: string;
  onBack: () => void;
}

export const EmergencyAckPage: React.FC<EmergencyAckPageProps> = ({ token, onBack }) => {
  const [acknowledged, setAcknowledged] = useState(false);
  const [ackData, setAckData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAcknowledge = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/incidents/ack/${token}`, {
        method: 'POST',
      });
      if (!res.ok) {
        throw new Error('Invalid or expired emergency token');
      }
      const data = await res.json();
      setAckData(data);
      setAcknowledged(true);
    } catch (err: any) {
      setError(err.message || 'Failed to acknowledge alert.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto w-full px-4 py-8 space-y-6">
      <div className="bg-white rounded-2xl shadow-xl border-2 border-emergency-red overflow-hidden">
        {/* Urgent Header */}
        <div className="bg-emergency-red text-white p-6 text-center space-y-2">
          <div className="w-12 h-12 rounded-full bg-white/20 mx-auto flex items-center justify-center animate-bounce">
            <AlertTriangle className="w-7 h-7 text-white" />
          </div>
          <h2 className="text-xl font-black uppercase tracking-wider">
            SafeHer Emergency SOS Alert
          </h2>
          <p className="text-xs text-white/90">
            A user has designated you as an emergency responder and triggered an active SOS alert.
          </p>
        </div>

        <div className="p-6 space-y-5">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs">
              {error}
            </div>
          )}

          {/* Acknowledgement Status */}
          {acknowledged ? (
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl space-y-2 text-center animate-in zoom-in">
              <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto" />
              <h4 className="font-bold text-emerald-900 text-sm">
                You Have Acknowledged This Alert!
              </h4>
              <p className="text-xs text-emerald-700">
                The sharer and their other contacts have been notified that you are responding.
              </p>
              {ackData && (
                <div className="text-[11px] text-slate-500 pt-2 border-t border-emerald-100 space-y-1">
                  <p><strong>Incident ID:</strong> {ackData.incident_id}</p>
                  <p><strong>Coordinates:</strong> {ackData.latitude?.toFixed(4)}, {ackData.longitude?.toFixed(4)}</p>
                  <p><strong>Time:</strong> {new Date(ackData.acknowledged_at).toLocaleTimeString()}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-2 text-xs">
                <div className="flex items-center gap-2 text-slate-700 font-semibold">
                  <Clock className="w-4 h-4 text-brand-500" />
                  <span>Immediate Action Required</span>
                </div>
                <p className="text-slate-600">
                  Please confirm whether you are able to respond to this emergency. Tapping below lets the sender know their distress signal was received.
                </p>
              </div>

              <button
                type="button"
                disabled={loading}
                onClick={handleAcknowledge}
                className="w-full py-4 bg-emerald-600 hover:bg-emerald-700 text-white font-black text-sm uppercase tracking-wider rounded-xl shadow-lg transition-transform active:scale-95 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-70"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    <CheckCircle2 className="w-5 h-5" />
                    <span>I AM RESPONDING / ACKNOWLEDGE</span>
                  </>
                )}
              </button>
            </div>
          )}

          {/* Location Deep Link */}
          {ackData?.map_deep_link && (
            <a
              href={ackData.map_deep_link}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 border border-slate-200"
            >
              <MapPin className="w-4 h-4 text-emergency-red" />
              <span>Open Location in Google Maps</span>
              <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
            </a>
          )}

          {/* Persistent Direct 112 Police Option */}
          <div className="pt-2 border-t border-slate-100">
            <a
              href="tel:112"
              className="w-full py-3 bg-emergency-red hover:bg-emergency-red-dark text-white rounded-xl font-bold text-xs uppercase tracking-wider shadow-md flex items-center justify-center gap-2"
            >
              <PhoneCall className="w-4 h-4" />
              <span>Call National Emergency (112)</span>
            </a>
          </div>
        </div>

        <div className="p-4 bg-slate-50 border-t border-slate-200 text-center">
          <button
            type="button"
            onClick={onBack}
            className="text-xs text-slate-500 hover:text-slate-800 flex items-center justify-center gap-1 mx-auto"
          >
            <Shield className="w-3.5 h-3.5" />
            <span>Return to SafeHer App</span>
          </button>
        </div>
      </div>
    </div>
  );
};
