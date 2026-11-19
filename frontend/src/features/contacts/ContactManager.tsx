import React, { useEffect, useState } from 'react';
import {
  Users,
  Plus,
  Phone,
  Trash2,
  CheckCircle2,
  Clock,
  Copy,
  Check,
  Shield,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { AddContactModal } from './AddContactModal';

export interface ContactItem {
  id: string;
  user_id: string;
  name: string;
  phone_number: string;
  email: string | null;
  relationship: string;
  priority: number;
  location_permission: string;
  is_verified: boolean;
  is_active: boolean;
  verification_token?: string;
  created_at: string;
}

export const ContactManager: React.FC = () => {
  const { token, isAuthenticated } = useAuth();
  const [contacts, setContacts] = useState<ContactItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [copiedToken, setCopiedToken] = useState<string | null>(null);

  const fetchContacts = async () => {
    if (!token) return;
    try {
      const res = await fetch('http://localhost:8000/api/v1/contacts', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setContacts(data);
      }
    } catch {
      // Fallback
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContacts();
  }, [token]);

  const handleDelete = async (contactId: string) => {
    if (!token) return;
    if (confirm('Are you sure you want to remove this emergency contact?')) {
      const res = await fetch(`http://localhost:8000/api/v1/contacts/${contactId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        fetchContacts();
      }
    }
  };

  const handleCopyVerificationLink = (tokenStr?: string) => {
    if (!tokenStr) return;
    const url = `${window.location.origin}/contact/verify/${tokenStr}`;
    navigator.clipboard.writeText(url);
    setCopiedToken(tokenStr);
    setTimeout(() => setCopiedToken(null), 2500);
  };

  if (!isAuthenticated) {
    return (
      <div className="bg-white p-6 rounded-2xl border border-slate-200 text-center space-y-3">
        <Users className="w-10 h-10 text-slate-300 mx-auto" />
        <h3 className="font-bold text-slate-900 text-base">Sign In to Manage Emergency Contacts</h3>
        <p className="text-xs text-slate-500 max-w-sm mx-auto">
          Add trusted family members or friends who will receive automated SOS alerts and location coordinates.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-pink-100 text-brand-600 flex items-center justify-center font-bold">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-base">Trusted Emergency Contacts</h3>
            <p className="text-xs text-slate-500">
              {contacts.length} of 5 contacts configured (Sorted by escalation priority)
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setIsAddModalOpen(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>Add Contact</span>
        </button>
      </div>

      {loading ? (
        <div className="py-6 text-center text-xs text-slate-400">Loading emergency contacts...</div>
      ) : contacts.length === 0 ? (
        <div className="py-8 text-center space-y-2">
          <Shield className="w-8 h-8 text-slate-300 mx-auto" />
          <p className="text-xs font-semibold text-slate-700">No emergency contacts added yet</p>
          <p className="text-[11px] text-slate-500 max-w-xs mx-auto">
            Add at least one primary responder so they can be alerted when you activate SOS or start a monitored journey.
          </p>
          <button
            type="button"
            onClick={() => setIsAddModalOpen(true)}
            className="text-xs text-brand-600 font-semibold underline mt-2"
          >
            Add Your First Contact
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {contacts.map((contact) => (
            <div
              key={contact.id}
              className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-white border border-slate-200 flex items-center justify-center font-bold text-slate-700 text-xs">
                  #{contact.priority}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900 text-sm">{contact.name}</span>
                    <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-slate-200 text-slate-700">
                      {contact.relationship}
                    </span>
                    {contact.is_verified ? (
                      <span className="inline-flex items-center gap-1 text-[10px] text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded-full">
                        <CheckCircle2 className="w-3 h-3" /> Verified
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[10px] text-amber-700 font-semibold bg-amber-50 px-2 py-0.5 rounded-full">
                        <Clock className="w-3 h-3" /> Consent Pending
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-slate-500 mt-1 text-[11px]">
                    <span className="flex items-center gap-1">
                      <Phone className="w-3 h-3 text-slate-400" />
                      {contact.phone_number}
                    </span>
                    <span className="text-slate-400">•</span>
                    <span>Scope: {contact.location_permission.replace('_', ' ')}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 self-end sm:self-center">
                {!contact.is_verified && contact.verification_token && (
                  <button
                    type="button"
                    onClick={() => handleCopyVerificationLink(contact.verification_token)}
                    title="Copy Consent & Verification Link to share with contact"
                    className="flex items-center gap-1 px-2.5 py-1 bg-white border border-slate-200 text-slate-700 rounded-lg text-[11px] font-medium hover:bg-slate-50"
                  >
                    {copiedToken === contact.verification_token ? (
                      <>
                        <Check className="w-3 h-3 text-emerald-600" />
                        <span className="text-emerald-600">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3 h-3" />
                        <span>Copy Link</span>
                      </>
                    )}
                  </button>
                )}

                <button
                  type="button"
                  onClick={() => handleDelete(contact.id)}
                  className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  aria-label="Delete contact"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <AddContactModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onContactAdded={fetchContacts}
        token={token}
      />
    </div>
  );
};
