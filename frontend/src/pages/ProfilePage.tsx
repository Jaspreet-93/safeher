import React, { useEffect, useState } from 'react';
import {
  User,
  Heart,
  Save,
  LogOut,
  AlertTriangle,
  History,
  CheckCircle2,
  Trash2,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export const ProfilePage: React.FC = () => {
  const { user, token, logout } = useAuth();
  const [profile, setProfile] = useState<any>(null);
  const [consents, setConsents] = useState<any[]>([]);
  const [bloodGroup, setBloodGroup] = useState('');
  const [emergencyNotes, setEmergencyNotes] = useState('');
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;

    // Fetch user profile
    fetch('http://localhost:8000/api/v1/users/me', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then((data) => {
        setProfile(data);
        if (data.profile) {
          setBloodGroup(data.profile.blood_group || '');
          setEmergencyNotes(data.profile.emergency_notes || '');
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));

    // Fetch consent audit history
    fetch('http://localhost:8000/api/v1/consent/history', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) setConsents(data);
      })
      .catch(() => {});
  }, [token]);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    const res = await fetch('http://localhost:8000/api/v1/users/me/profile', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        blood_group: bloodGroup,
        emergency_notes: emergencyNotes,
      }),
    });

    if (res.ok) {
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    }
  };

  const handleRevokeAllSessions = async () => {
    if (!token) return;
    if (confirm('This will immediately terminate all active logins across all your devices. Continue?')) {
      await fetch('http://localhost:8000/api/v1/auth/sessions/revoke-all', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      await logout();
    }
  };

  const handleDeleteAccount = async () => {
    if (!token) return;
    if (
      confirm(
        'Are you sure you want to delete your SafeHer account? All active sessions will be terminated and personal data staged for permanent erasure.'
      )
    ) {
      await fetch('http://localhost:8000/api/v1/users/me', {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      await logout();
    }
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12 text-center text-slate-500 text-sm">
        Loading profile and privacy settings...
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      {/* Account Identity Card */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-brand-100 text-brand-600 flex items-center justify-center font-bold text-xl">
            <User className="w-7 h-7" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">
              {profile?.profile?.full_name || user?.email}
            </h2>
            <p className="text-sm text-slate-500">{user?.email}</p>
            <div className="flex gap-2 mt-1">
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                Role: {user?.role}
              </span>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700">
                Active Session
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={logout}
            className="flex items-center gap-1.5 px-4 py-2 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold transition-colors"
          >
            <LogOut className="w-4 h-4 text-slate-500" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Voluntary Medical & Emergency Profile */}
        <form
          onSubmit={handleSaveProfile}
          className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4"
        >
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <Heart className="w-5 h-5 text-emergency-red" />
            <div>
              <h3 className="font-bold text-slate-900 text-base">Emergency Medical Profile</h3>
              <p className="text-xs text-slate-500">Voluntary info shared with first responders in an SOS</p>
            </div>
          </div>

          {savedSuccess && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-lg text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>Medical profile updated successfully.</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Blood Group</label>
            <select
              value={bloodGroup}
              onChange={(e) => setBloodGroup(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="">Select Blood Group (Optional)</option>
              <option value="A+">A+</option>
              <option value="A-">A-</option>
              <option value="B+">B+</option>
              <option value="B-">B-</option>
              <option value="O+">O+</option>
              <option value="O-">O-</option>
              <option value="AB+">AB+</option>
              <option value="AB-">AB-</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Allergies & Critical Notes
            </label>
            <textarea
              rows={3}
              value={emergencyNotes}
              onChange={(e) => setEmergencyNotes(e.target.value)}
              placeholder="e.g. Allergic to penicillin, diabetic, asthmatic"
              className="w-full p-3 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          <button
            type="submit"
            className="w-full py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-sm flex items-center justify-center gap-1.5 cursor-pointer"
          >
            <Save className="w-4 h-4" />
            <span>Save Emergency Information</span>
          </button>
        </form>

        {/* DPDPA 2023 Consent History & Audit */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <History className="w-5 h-5 text-brand-600" />
            <div>
              <h3 className="font-bold text-slate-900 text-base">DPDPA 2023 Consent Trail</h3>
              <p className="text-xs text-slate-500">Immutable audit log of your privacy grants</p>
            </div>
          </div>

          <div className="space-y-3 max-h-56 overflow-y-auto pr-1">
            {consents.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No consent history recorded yet.</p>
            ) : (
              consents.map((c) => (
                <div
                  key={c.id}
                  className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-800 uppercase tracking-wider text-[10px]">
                      {c.consent_type.replace(/_/g, ' ')} ({c.version})
                    </span>
                    <span className="text-[10px] text-emerald-600 font-bold bg-emerald-50 px-2 py-0.5 rounded-full">
                      GRANTED
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500">
                    Logged: {new Date(c.timestamp).toLocaleString()}
                  </p>
                </div>
              ))
            )}
          </div>

          <div className="pt-2 border-t border-slate-100 space-y-2">
            <button
              type="button"
              onClick={handleRevokeAllSessions}
              className="w-full py-2 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5"
            >
              <AlertTriangle className="w-4 h-4" />
              <span>Nuclear: Revoke All Device Sessions</span>
            </button>

            <button
              type="button"
              onClick={handleDeleteAccount}
              className="w-full py-2 bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5"
            >
              <Trash2 className="w-4 h-4" />
              <span>Delete Account & Erase Personal Data</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
