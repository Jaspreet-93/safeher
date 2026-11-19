import React from 'react';
import {
  X,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Server,
} from 'lucide-react';

export interface NotificationReceipt {
  id: string;
  contact_id: string;
  contact_name: string;
  recipient_address: string;
  channel: string;
  status: string; // queued, sent, delivered, failed, acknowledged
  provider_message_id?: string | null;
  sent_at?: string | null;
  delivered_at?: string | null;
  acknowledged_at?: string | null;
  failure_reason?: string | null;
}

interface DeliveryReceiptsModalProps {
  isOpen: boolean;
  onClose: () => void;
  notification: NotificationReceipt | null;
}

export const DeliveryReceiptsModal: React.FC<DeliveryReceiptsModalProps> = ({
  isOpen,
  onClose,
  notification,
}) => {
  if (!isOpen || !notification) return null;

  const isMockProvider =
    !notification.provider_message_id ||
    notification.provider_message_id.startsWith('mock-');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in">
      <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden border border-slate-200">
        {/* Header */}
        <div className="bg-slate-900 text-white p-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center text-rose-400">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base leading-tight">Delivery Audit Trail</h3>
              <p className="text-xs text-slate-400">
                Carrier DLR Receipts & Dispatch Telemetry
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Rule 5 Notice: Explicit Mock Tag */}
        {isMockProvider && (
          <div className="bg-amber-50 border-b border-amber-200 px-5 py-2.5 flex items-center gap-2 text-amber-800 text-xs font-medium">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>
              <strong>[MOCK CARRIER]</strong> Simulated telecom gateway dispatch in dev mode.
            </span>
          </div>
        )}

        {/* Content Body */}
        <div className="p-6 space-y-5 text-left text-xs">
          {/* Recipient Details */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-slate-500 font-medium">Recipient:</span>
              <span className="font-bold text-slate-900">{notification.contact_name}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-500 font-medium">Address / Phone:</span>
              <span className="font-mono text-slate-800">{notification.recipient_address}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-500 font-medium">Carrier Channel:</span>
              <span className="uppercase font-bold tracking-wider text-[11px] text-slate-700 bg-slate-200/70 px-2 py-0.5 rounded">
                {notification.channel}
              </span>
            </div>
          </div>

          {/* Status & Carrier Reference */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-slate-600 font-semibold">Delivery State:</span>
              <div>
                {notification.status === 'acknowledged' && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 font-bold text-xs">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Acknowledged by Contact
                  </span>
                )}
                {notification.status === 'delivered' && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-100 text-blue-800 font-bold text-xs">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Carrier Delivered (DLR OK)
                  </span>
                )}
                {notification.status === 'sent' && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 text-blue-700 font-bold text-xs">
                    <Clock className="w-3.5 h-3.5" /> Sent to Carrier Gateway
                  </span>
                )}
                {notification.status === 'queued' && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-100 text-amber-800 font-bold text-xs">
                    <Clock className="w-3.5 h-3.5" /> Queued in Outbox
                  </span>
                )}
                {notification.status === 'failed' && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-100 text-rose-800 font-bold text-xs">
                    <AlertTriangle className="w-3.5 h-3.5" /> Dispatch Failed
                  </span>
                )}
              </div>
            </div>

            <div className="p-3 bg-slate-100/70 rounded-xl space-y-1">
              <span className="text-[11px] text-slate-500 font-medium block">
                Carrier Transaction Reference (Message ID):
              </span>
              <p className="font-mono text-xs text-slate-900 break-all select-all font-semibold">
                {notification.provider_message_id || 'Pending Gateway Generation'}
              </p>
            </div>
          </div>

          {/* Timestamp Lifecycle */}
          <div className="border border-slate-200 rounded-xl p-4 space-y-2.5">
            <h4 className="font-bold text-slate-900 text-xs flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-slate-500" />
              <span>Telemetry Timestamp Trail</span>
            </h4>

            <div className="space-y-1.5 pt-1 text-[11px]">
              <div className="flex justify-between">
                <span className="text-slate-500">Gateway Sent Time:</span>
                <span className="font-mono text-slate-800">
                  {notification.sent_at
                    ? new Date(notification.sent_at).toLocaleTimeString()
                    : '—'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Carrier Handset DLR:</span>
                <span className="font-mono text-slate-800">
                  {notification.delivered_at
                    ? new Date(notification.delivered_at).toLocaleTimeString()
                    : 'Awaiting carrier webhook'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Guardian Ack Timestamp:</span>
                <span className="font-mono text-slate-800">
                  {notification.acknowledged_at
                    ? new Date(notification.acknowledged_at).toLocaleTimeString()
                    : 'Not acknowledged yet'}
                </span>
              </div>
            </div>
          </div>

          {/* Failure Diagnostic Box if failed */}
          {notification.failure_reason && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl space-y-1">
              <span className="font-bold text-rose-900 text-xs flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                <span>Failover & Gateway Error Diagnostic:</span>
              </span>
              <p className="text-rose-700 text-xs font-mono break-words">
                {notification.failure_reason}
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-slate-50 p-4 border-t border-slate-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold cursor-pointer shadow-sm transition-colors"
          >
            Close Audit Trail
          </button>
        </div>
      </div>
    </div>
  );
};
