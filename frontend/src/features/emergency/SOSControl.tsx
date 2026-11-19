import React, { useState, useEffect } from 'react';
import {
  AlertOctagon,
  XCircle,
  PhoneCall,
  CheckCircle2,
  Clock,
  Radio,
  WifiOff,
  Navigation,
  Loader2,
  MessageSquare,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useGeolocation } from '../../hooks/useGeolocation';
import { useOfflineOutbox } from '../../hooks/useOfflineOutbox';
import { DeliveryReceiptsModal, NotificationReceipt } from './DeliveryReceiptsModal';

export const SOSControl: React.FC = () => {
  const { token, isAuthenticated } = useAuth();
  const geo = useGeolocation(true);
  const { isOnline, queueOfflineSOS, getNativeSmsFallbackUrl } = useOfflineOutbox();

  // SOS States: idle | countdown | active | cancelled | resolved
  const [sosState, setSosState] = useState<'idle' | 'countdown' | 'active' | 'cancelled' | 'resolved'>('idle');
  const [countdownSeconds, setCountdownSeconds] = useState(5);
  const [incidentData, setIncidentData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [offlineNotice, setOfflineNotice] = useState(false);
  const [selectedReceipt, setSelectedReceipt] = useState<NotificationReceipt | null>(null);

  // Countdown timer effect
  useEffect(() => {
    let interval: any = null;
    if (sosState === 'countdown') {
      interval = setInterval(() => {
        setCountdownSeconds((prev) => {
          if (prev <= 1) {
            clearInterval(interval);
            activateIncident();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [sosState]);

  // Periodic poll of incident delivery status when active
  useEffect(() => {
    let pollInterval: any = null;
    if (sosState === 'active' && incidentData?.id && token) {
      pollInterval = setInterval(async () => {
        try {
          const res = await fetch(`http://localhost:8000/api/v1/incidents/${incidentData.id}/status`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (res.ok) {
            const data = await res.json();
            setIncidentData(data);
          }
        } catch {
          // Keep current state if network blips
        }
      }, 3000);
    }
    return () => clearInterval(pollInterval);
  }, [sosState, incidentData?.id, token]);

  const handleStartSOS = async () => {
    const lat = geo.latitude || 28.6139; // Default fallback to New Delhi if GPS blocked
    const lng = geo.longitude || 77.2090;

    // Check offline fail-loudly rule
    if (!isOnline) {
      const offlineKey = `offline-${Date.now()}`;
      queueOfflineSOS({
        idempotencyKey: offlineKey,
        latitude: lat,
        longitude: lng,
        accuracy: geo.accuracy,
        timestamp: new Date().toISOString(),
      });
      setOfflineNotice(true);
      return;
    }

    if (!isAuthenticated || !token) {
      alert("Please sign in first so your emergency contacts can be alerted.");
      return;
    }

    setLoading(true);
    setCountdownSeconds(5);

    try {
      const idempotencyKey = `sos-${Date.now()}-${Math.random().toString(36).substring(7)}`;
      const res = await fetch('http://localhost:8000/api/v1/incidents/sos', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          'X-Idempotency-Key': idempotencyKey,
        },
        body: JSON.stringify({
          latitude: lat,
          longitude: lng,
          accuracy_meters: geo.accuracy || 10.0,
          grace_period_seconds: 5,
        }),
      });

      if (!res.ok) {
        throw new Error('Failed to initiate emergency incident.');
      }

      const data = await res.json();
      setIncidentData(data);
      setSosState('countdown');
    } catch (err: any) {
      alert(err.message || 'Error triggering SOS');
    } finally {
      setLoading(false);
    }
  };

  const activateIncident = async () => {
    if (!incidentData?.id || !token) return;
    try {
      const res = await fetch(`http://localhost:8000/api/v1/incidents/${incidentData.id}/activate`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setIncidentData(data);
        setSosState('active');
      }
    } catch {
      setSosState('active');
    }
  };

  const handleCancelSOS = async () => {
    if (!incidentData?.id || !token) {
      setSosState('idle');
      return;
    }

    try {
      await fetch(`http://localhost:8000/api/v1/incidents/${incidentData.id}/cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ cancel_reason: 'User cancelled during grace countdown' }),
      });
    } catch {
      // Handled
    }

    setSosState('cancelled');
    setTimeout(() => {
      setSosState('idle');
      setIncidentData(null);
    }, 2500);
  };

  const handleResolveSOS = async () => {
    if (!incidentData?.id || !token) return;
    try {
      await fetch(`http://localhost:8000/api/v1/incidents/${incidentData.id}/resolve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ resolution_notes: 'User verified safety.' }),
      });
    } catch {
      // Handled
    }

    setSosState('resolved');
    setTimeout(() => {
      setSosState('idle');
      setIncidentData(null);
    }, 2500);
  };

  return (
    <section className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-slate-200 text-center relative overflow-hidden">
      {/* Offline Fail-Loudly Warning Modal */}
      {offlineNotice && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in">
          <div className="bg-slate-900 text-white rounded-2xl max-w-md w-full p-6 border-2 border-emergency-red text-center space-y-4">
            <div className="w-14 h-14 rounded-full bg-emergency-red/20 text-emergency-red mx-auto flex items-center justify-center">
              <WifiOff className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-black text-emergency-red uppercase tracking-wider">
              NOT SENT — NO INTERNET CONNECTION
            </h3>
            <p className="text-xs text-slate-300">
              SafeHer queued your alert locally, but cannot reach remote servers or dispatch telecom SMS without cellular data.
            </p>

            <div className="space-y-3 pt-2">
              <a
                href="tel:112"
                className="w-full py-3 bg-emergency-red hover:bg-emergency-red-dark text-white rounded-xl font-bold text-base flex items-center justify-center gap-2 shadow-lg"
              >
                <PhoneCall className="w-5 h-5 animate-bounce" />
                <span>Call 112 Police / ERSS Directly</span>
              </a>

              <a
                href={getNativeSmsFallbackUrl(
                  '112',
                  geo.latitude,
                  geo.longitude
                )}
                className="w-full py-2.5 bg-slate-800 hover:bg-slate-700 text-white border border-slate-600 rounded-xl font-semibold text-xs flex items-center justify-center gap-2"
              >
                <MessageSquare className="w-4 h-4" />
                <span>Open Phone SMS Composer with GPS</span>
              </a>

              <button
                type="button"
                onClick={() => setOfflineNotice(false)}
                className="w-full py-2 text-slate-400 hover:text-white text-xs"
              >
                Dismiss Warning
              </button>
            </div>
          </div>
        </div>
      )}

      {/* State 1: IDLE */}
      {sosState === 'idle' && (
        <div className="max-w-2xl mx-auto space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-50 text-emergency-red text-xs font-semibold">
            <Radio className="w-3.5 h-3.5 animate-pulse" />
            <span>Emergency Rapid Response Ready</span>
          </div>

          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            One-Thumb Emergency SOS
          </h2>
          <p className="text-xs sm:text-sm text-slate-600 max-w-lg mx-auto">
            Dispatches your live coordinates to priority emergency contacts via SMS and prepares escalation if unacknowledged.
          </p>

          <div className="pt-4 flex flex-col items-center justify-center gap-3">
            <button
              type="button"
              disabled={loading}
              onClick={handleStartSOS}
              className="w-48 h-48 rounded-full bg-emergency-red hover:bg-emergency-red-dark text-white font-black text-2xl tracking-wider shadow-2xl flex flex-col items-center justify-center gap-2 transform active:scale-95 transition-all animate-emergency-ring focus:outline-none focus:ring-8 focus:ring-emergency-red/30 cursor-pointer disabled:opacity-70"
              aria-label="Trigger Emergency SOS"
            >
              {loading ? (
                <Loader2 className="w-12 h-12 animate-spin" />
              ) : (
                <>
                  <AlertOctagon className="w-16 h-16 stroke-[2.5]" />
                  <span>TRIGGER SOS</span>
                </>
              )}
            </button>
            <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
              <Navigation className="w-3.5 h-3.5 text-brand-500" />
              <span>
                GPS Accuracy: {geo.accuracy ? `±${Math.round(geo.accuracy)}m` : 'Acquiring location...'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* State 2: COUNTDOWN GRACE WINDOW */}
      {sosState === 'countdown' && (
        <div className="max-w-md mx-auto space-y-5 animate-in zoom-in duration-150">
          <div className="w-24 h-24 rounded-full bg-emergency-red text-white font-black text-4xl flex items-center justify-center mx-auto shadow-2xl animate-ping">
            {countdownSeconds}
          </div>

          <div>
            <h3 className="text-xl font-extrabold text-slate-900">Activating SOS in {countdownSeconds}s...</h3>
            <p className="text-xs text-slate-500 mt-1">
              If this was triggered accidentally, tap cancel now. No SMS has been dispatched yet.
            </p>
          </div>

          <button
            type="button"
            onClick={handleCancelSOS}
            className="w-full py-3.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl font-bold text-sm shadow-lg flex items-center justify-center gap-2 cursor-pointer"
          >
            <XCircle className="w-5 h-5 text-emergency-red" />
            <span>CANCEL SOS (ACCIDENTAL)</span>
          </button>
        </div>
      )}

      {/* State 3: ACTIVE EMERGENCY */}
      {sosState === 'active' && (
        <div className="max-w-xl mx-auto space-y-6 text-left animate-in fade-in">
          <div className="bg-red-50 border border-red-200 p-4 rounded-xl flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="w-3 h-3 rounded-full bg-emergency-red animate-ping" />
              <div>
                <span className="font-bold text-emergency-red text-sm uppercase tracking-wider">
                  SOS Incident Active
                </span>
                <p className="text-[11px] text-slate-600">
                  Coordinates transmitted: {incidentData?.latitude?.toFixed(4)}, {incidentData?.longitude?.toFixed(4)}
                </p>
              </div>
            </div>

            <a
              href="tel:112"
              className="px-3 py-1.5 bg-emergency-red hover:bg-emergency-red-dark text-white rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-sm"
            >
              <PhoneCall className="w-3.5 h-3.5" />
              <span>Call 112</span>
            </a>
          </div>

          {/* Delivery Receipts per Contact */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              Emergency Contact Delivery Status:
            </h4>

            {incidentData?.notifications?.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No verified contacts available to alert.</p>
            ) : (
              incidentData?.notifications?.map((notif: any) => (
                <div
                  key={notif.id}
                  onClick={() => setSelectedReceipt(notif)}
                  title="Click to view carrier delivery audit trail"
                  className="p-3 bg-slate-50 hover:bg-slate-100/80 border border-slate-200 hover:border-slate-300 rounded-xl flex items-center justify-between text-xs cursor-pointer transition-colors"
                >
                  <div>
                    <span className="font-bold text-slate-900">{notif.contact_name}</span>
                    <span className="text-slate-500 text-[11px] block">{notif.recipient_address}</span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    {notif.status === 'acknowledged' ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold text-[10px]">
                        <CheckCircle2 className="w-3 h-3" /> Responding / Acknowledged
                      </span>
                    ) : notif.status === 'delivered' ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-800 font-bold text-[10px]">
                        <CheckCircle2 className="w-3 h-3" /> Carrier Delivered
                      </span>
                    ) : notif.status === 'sent' ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 font-bold text-[10px]">
                        <Clock className="w-3 h-3" /> Sent to Gateway
                      </span>
                    ) : notif.status === 'failed' ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-800 font-bold text-[10px]">
                        <XCircle className="w-3 h-3" /> Failed (View Log)
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-800 font-bold text-[10px]">
                        <Clock className="w-3 h-3" /> Queued / Retrying
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Resolve Control */}
          <div className="pt-2">
            <button
              type="button"
              onClick={handleResolveSOS}
              className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs uppercase tracking-wider shadow-md flex items-center justify-center gap-2 cursor-pointer"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>I Am Safe (Resolve Incident)</span>
            </button>
          </div>
        </div>
      )}

      {/* State 4 & 5: Cancelled or Resolved confirmations */}
      {sosState === 'cancelled' && (
        <div className="py-8 space-y-2 text-center animate-in fade-in">
          <XCircle className="w-12 h-12 text-slate-400 mx-auto" />
          <h3 className="font-bold text-slate-800 text-base">Incident Cancelled</h3>
          <p className="text-xs text-slate-500">Grace period aborted. Zero notifications were dispatched.</p>
        </div>
      )}

      {sosState === 'resolved' && (
        <div className="py-8 space-y-2 text-center animate-in fade-in">
          <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto" />
          <h3 className="font-bold text-slate-900 text-base">Incident Resolved Safely</h3>
          <p className="text-xs text-slate-500">Glad you are safe! Notifications updated.</p>
        </div>
      )}

      {/* Delivery Receipts Modal for In-depth Audit Trail */}
      <DeliveryReceiptsModal
        isOpen={!!selectedReceipt}
        onClose={() => setSelectedReceipt(null)}
        notification={selectedReceipt}
      />
    </section>
  );
};
