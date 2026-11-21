import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export interface SafePlaceMapItem {
  id: string;
  name: string;
  category: string;
  latitude: number;
  longitude: number;
  address?: string;
  phone_number?: string;
  is_24_7: boolean;
  is_verified: boolean;
  safety_score?: number;
  distance_km?: number;
}

interface SafePlacesMapProps {
  places: SafePlaceMapItem[];
  userLat: number;
  userLng: number;
  onPlaceSelect: (place: SafePlaceMapItem) => void;
  selectedPlaceId?: string | null;
}

// Category icon colors and unicode symbols
const CATEGORY_CONFIG: Record<string, { color: string; emoji: string; label: string }> = {
  police_station:  { color: '#1e40af', emoji: '🚔', label: 'Police' },
  hospital_24_7:   { color: '#065f46', emoji: '🏥', label: 'Hospital' },
  women_helpdesk:  { color: '#7e22ce', emoji: '💜', label: "Women's Help" },
  pharmacy:        { color: '#0369a1', emoji: '💊', label: 'Pharmacy' },
  transit_hub:     { color: '#92400e', emoji: '🚇', label: 'Transit' },
  verified_shelter:{ color: '#b91c1c', emoji: '🏠', label: 'Shelter' },
};

function createPlaceIcon(category: string, isSelected: boolean): L.DivIcon {
  const cfg = CATEGORY_CONFIG[category] ?? { color: '#374151', emoji: '📍', label: 'Place' };
  const size = isSelected ? 48 : 36;
  const ring = isSelected ? `box-shadow:0 0 0 3px ${cfg.color}60;` : '';
  return L.divIcon({
    className: '',
    html: `<div style="
      width:${size}px;height:${size}px;border-radius:50%;
      background:${cfg.color};color:#fff;
      display:flex;align-items:center;justify-content:center;
      font-size:${isSelected ? 22 : 16}px;
      border:2.5px solid #fff;
      ${ring}
      transition:all .2s ease;
    ">${cfg.emoji}</div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

function createUserIcon(): L.DivIcon {
  return L.divIcon({
    className: '',
    html: `<div style="
      width:18px;height:18px;border-radius:50%;
      background:#ef4444;border:3px solid #fff;
      box-shadow:0 0 0 4px rgba(239,68,68,0.3);
    "></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });
}

export const SafePlacesMap: React.FC<SafePlacesMapProps> = ({
  places,
  userLat,
  userLng,
  onPlaceSelect,
  selectedPlaceId,
}) => {
  const mapRef = useRef<HTMLDivElement>(null);
  const leafletMap = useRef<L.Map | null>(null);
  const markersRef = useRef<Map<string, L.Marker>>(new Map());

  // Initialize map
  useEffect(() => {
    if (!mapRef.current || leafletMap.current) return;

    const map = L.map(mapRef.current, {
      center: [userLat, userLng],
      zoom: 14,
      zoomControl: true,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(map);

    // User marker
    L.marker([userLat, userLng], { icon: createUserIcon(), zIndexOffset: 1000 })
      .addTo(map)
      .bindPopup('<strong>📍 Your location</strong>');

    // Accuracy circle (~100m visual aid)
    L.circle([userLat, userLng], {
      radius: 100,
      color: '#ef4444',
      fillColor: '#ef4444',
      fillOpacity: 0.08,
      weight: 1,
    }).addTo(map);

    leafletMap.current = map;
    return () => {
      map.remove();
      leafletMap.current = null;
    };
  }, [userLat, userLng]);

  // Update place markers
  useEffect(() => {
    const map = leafletMap.current;
    if (!map) return;

    // Remove stale markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current.clear();

    places.forEach((place) => {
      const isSelected = place.id === selectedPlaceId;
      const icon = createPlaceIcon(place.category, isSelected);
      const cfg = CATEGORY_CONFIG[place.category] ?? { label: 'Place', emoji: '📍', color: '#374151' };
      const distText = place.distance_km != null ? `${place.distance_km.toFixed(2)} km away` : '';
      const scoreText = place.safety_score != null ? `⭐ ${place.safety_score.toFixed(1)}` : '';

      const popup = L.popup({ maxWidth: 240 }).setContent(`
        <div style="font-family:Inter,sans-serif;font-size:13px;line-height:1.5">
          <div style="font-weight:700;color:#111;margin-bottom:4px">${cfg.emoji} ${place.name}</div>
          <div style="color:#6b7280;font-size:11px;margin-bottom:6px">${cfg.label} · ${distText} ${scoreText}</div>
          ${place.address ? `<div style="color:#374151;font-size:11px;margin-bottom:4px">📍 ${place.address}</div>` : ''}
          ${place.phone_number ? `<a href="tel:${place.phone_number}" style="display:inline-block;margin-top:4px;padding:3px 10px;background:${cfg.color};color:#fff;border-radius:6px;text-decoration:none;font-size:11px;font-weight:600">📞 ${place.phone_number}</a>` : ''}
          ${place.is_24_7 ? `<span style="display:inline-block;margin:4px 0 0 6px;font-size:10px;padding:2px 6px;background:#d1fae5;color:#065f46;border-radius:4px;font-weight:600">24/7</span>` : ''}
          ${place.is_verified ? `<span style="display:inline-block;margin:4px 0 0 6px;font-size:10px;padding:2px 6px;background:#dbeafe;color:#1e40af;border-radius:4px;font-weight:600">✓ Verified</span>` : ''}
        </div>
      `);

      const marker = L.marker([place.latitude, place.longitude], {
        icon,
        zIndexOffset: isSelected ? 500 : 0,
      })
        .addTo(map)
        .bindPopup(popup)
        .on('click', () => onPlaceSelect(place));

      markersRef.current.set(place.id, marker);
    });
  }, [places, selectedPlaceId, onPlaceSelect]);

  // Pan to selected place
  useEffect(() => {
    if (!selectedPlaceId || !leafletMap.current) return;
    const marker = markersRef.current.get(selectedPlaceId);
    if (marker) {
      leafletMap.current.panTo(marker.getLatLng(), { animate: true });
      marker.openPopup();
    }
  }, [selectedPlaceId]);

  return (
    <div
      ref={mapRef}
      id="safe-places-map"
      style={{ width: '100%', height: '100%', borderRadius: '16px', zIndex: 0 }}
    />
  );
};
