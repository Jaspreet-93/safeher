import React from 'react';
import { ShieldCheck, X, FileText, CheckCircle } from 'lucide-react';

interface ConsentNoticeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ConsentNoticeModal: React.FC<ConsentNoticeModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl relative border border-slate-200 animate-in fade-in zoom-in duration-200">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1 rounded-lg"
          aria-label="Close modal"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-pink-100 text-brand-600 flex items-center justify-center">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900">Privacy Notice & Consent Baseline</h3>
            <p className="text-xs text-slate-500">In compliance with Digital Personal Data Protection Act, 2023</p>
          </div>
        </div>

        <div className="space-y-4 text-sm text-slate-600 max-h-96 overflow-y-auto pr-2">
          <div className="bg-pink-50/60 p-3 rounded-lg border border-pink-100 flex gap-2">
            <CheckCircle className="w-4 h-4 text-brand-600 shrink-0 mt-0.5" />
            <p className="text-xs text-brand-900">
              <strong>Strict Purpose Limitation:</strong> Your location telemetry and emergency triggers are used exclusively to protect you during active journeys and SOS incidents.
            </p>
          </div>

          <div className="space-y-2">
            <h4 className="font-semibold text-slate-800 flex items-center gap-1.5 text-xs uppercase tracking-wider">
              <FileText className="w-4 h-4 text-slate-500" /> Key Privacy Guarantees
            </h4>
            <ul className="list-disc pl-5 space-y-1.5 text-xs text-slate-600">
              <li><strong>Zero Commercial Monetization:</strong> We never sell, broker, or share your coordinates for advertising or cross-site behavioral profiling.</li>
              <li><strong>Time-Bounded & Revocable:</strong> Live location sharing links expire automatically and can be revoked instantly at any moment.</li>
              <li><strong>No Secret Tracking:</strong> Employers or college administrators cannot view your real-time whereabouts unless you explicitly opt in to institutional emergency escalation.</li>
              <li><strong>Right to Complete Erasure:</strong> You can delete your account at any time, which permanently destroys all session tokens and personal identifiers.</li>
            </ul>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-slate-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-sm font-semibold transition-colors"
          >
            I Understand & Agree
          </button>
        </div>
      </div>
    </div>
  );
};
