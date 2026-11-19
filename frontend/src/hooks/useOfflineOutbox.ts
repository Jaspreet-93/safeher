import { useState, useEffect, useCallback } from 'react';

export interface OfflineSOSItem {
  idempotencyKey: string;
  latitude: number;
  longitude: number;
  accuracy: number | null;
  timestamp: string;
}

export const useOfflineOutbox = () => {
  const [isOnline, setIsOnline] = useState<boolean>(navigator.onLine);
  const [pendingItems, setPendingItems] = useState<OfflineSOSItem[]>([]);

  // Load pending offline items from storage
  useEffect(() => {
    const saved = localStorage.getItem('safeher_offline_outbox');
    if (saved) {
      try {
        setPendingItems(JSON.parse(saved));
      } catch {
        localStorage.removeItem('safeher_offline_outbox');
      }
    }

    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Save to storage
  const savePending = useCallback((items: OfflineSOSItem[]) => {
    setPendingItems(items);
    localStorage.setItem('safeher_offline_outbox', JSON.stringify(items));
  }, []);

  // Queue an offline SOS item
  const queueOfflineSOS = useCallback(
    (item: OfflineSOSItem) => {
      const updated = [...pendingItems, item];
      savePending(updated);
    },
    [pendingItems, savePending]
  );

  // Clear offline outbox item
  const clearOfflineSOS = useCallback(
    (idempotencyKey: string) => {
      const updated = pendingItems.filter((i) => i.idempotencyKey !== idempotencyKey);
      savePending(updated);
    },
    [pendingItems, savePending]
  );

  // Helper to generate native SMS fallback URL pre-filled with emergency message
  const getNativeSmsFallbackUrl = (toPhone: string, lat: number | null, lng: number | null) => {
    const locText = lat && lng ? `https://maps.google.com/?q=${lat},${lng}` : 'Location unavailable';
    const body = encodeURIComponent(
      `SAFEHER EMERGENCY: I need immediate assistance! My current location: ${locText}. Please call me or 112.`
    );
    // Universal SMS URL scheme
    return `sms:${toPhone}?body=${body}`;
  };

  return {
    isOnline,
    hasPendingOfflineAlert: pendingItems.length > 0,
    pendingItems,
    queueOfflineSOS,
    clearOfflineSOS,
    getNativeSmsFallbackUrl,
  };
};
