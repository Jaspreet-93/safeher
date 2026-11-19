import React, { useState } from 'react';
import { X, User, Phone, Mail, ShieldAlert, Loader2 } from 'lucide-react';

interface AddContactModalProps {
  isOpen: boolean;
  onClose: () => void;
  onContactAdded: () => void;
  token: string | null;
}

export const AddContactModal: React.FC<AddContactModalProps> = ({
  isOpen,
  onClose,
  onContactAdded,
  token,
}) => {
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [relationship, setRelationship] = useState('family');
  const [priority, setPriority] = useState<number>(1);
  const [locationPermission, setLocationPermission] = useState('sos_only');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    setError(null);
    setLoading(true);

    try {
      const res = await fetch('http://localhost:8000/api/v1/contacts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name,
          phone_number: phone,
          email: email || null,
          relationship,
          priority,
          location_permission: locationPermission,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.message || 'Failed to add contact');
      }

      onContactAdded();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Error adding contact');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in">
      <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl relative border border-slate-200">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1 rounded-lg"
          aria-label="Close"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-brand-100 text-brand-600 flex items-center justify-center">
            <User className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900">Add Trusted Emergency Contact</h3>
            <p className="text-xs text-slate-500">Will receive alerts and coordinates during SOS</p>
          </div>
        </div>

        {error && (
          <div className="p-3 mb-4 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Contact Name *
            </label>
            <div className="relative">
              <User className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Mom / Priya / Officer"
                className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Mobile Phone Number (SMS Alert Recipient) *
            </label>
            <div className="relative">
              <Phone className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="tel"
                required
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+91 98765 43210"
                className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Relationship
              </label>
              <select
                value={relationship}
                onChange={(e) => setRelationship(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="parent">Parent</option>
                <option value="spouse">Spouse / Partner</option>
                <option value="sibling">Sibling</option>
                <option value="friend">Friend</option>
                <option value="colleague">Colleague</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Priority Tier
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value={1}>1 (Primary Responder)</option>
                <option value={2}>2 (Secondary)</option>
                <option value={3}>3 (Escalation Tier)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Email Address (Optional)
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="contact@example.com"
                className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>

          {/* Granular Location Permission Scope */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Location Sharing Scope (Consent First)
            </label>
            <select
              value={locationPermission}
              onChange={(e) => setLocationPermission(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="sos_only">SOS Only (Coordinates sent only during active SOS)</option>
              <option value="journeys">Journeys & SOS (Coordinates during shared trips and SOS)</option>
              <option value="none">No Location (Receive text alert without GPS coordinates)</option>
            </select>
            <p className="text-[11px] text-slate-500 mt-1">
              In accordance with SafeHer's privacy policy, contacts never receive continuous background location.
            </p>
          </div>

          <div className="pt-2 flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2 border border-slate-200 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-xs font-semibold shadow-md flex items-center justify-center gap-1.5 disabled:opacity-70"
            >
              {loading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Adding...</span>
                </>
              ) : (
                <>
                  <ShieldAlert className="w-3.5 h-3.5" />
                  <span>Save Contact</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
