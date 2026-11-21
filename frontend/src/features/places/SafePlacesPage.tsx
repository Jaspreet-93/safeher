import React, { useCallback, useEffect, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  ExternalLink,
  Loader2,
  MapPin,
  Navigation,
  Phone,
  Search,
  Shield,
  Star,
  WifiOff,
} from 'lucide-react';
import { SafePlacesMap, SafePlaceMapItem } from './SafePlacesMap';
import { useGeolocation } from '../../hooks/useGeolocation';

// ─────────────────────────── Category metadata ───────────────────────────────
const CATEGORIES = [
  { key: null,               label: 'All',          emoji: '🗺️' },
  { key: 'police_station',   label: 'Police',        emoji: '🚔' },
  { key: 'hospital_24_7',    label: 'Hospitals',     emoji: '🏥' },
  { key: 'women_helpdesk',   label: "Women's Help",  emoji: '💜' },
  { key: 'pharmacy',         label: 'Pharmacy',      emoji: '💊' },
  { key: 'transit_hub',      label: 'Transit',       emoji: '🚇' },
  { key: 'verified_shelter', label: 'Shelters',      emoji: '🏠' },
];

type Place = SafePlaceMapItem & {
  address?: string;
  phone_number?: string;
  operating_hours?: string;
  verified_by?: string;
  review_count?: number;
};

// ─────────────────────────── Main Page ───────────────────────────────────────
export const SafePlacesPage: React.FC = () => {
  const geo = useGeolocation(true);

  const [places, setPlaces] = useState<Place[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedPlace, setSelectedPlace] = useState<Place | null>(null);
  const [radiusKm, setRadiusKm] = useState(5);
  const [verifiedOnly, setVerifiedOnly] = useState(false);

  // Use user GPS or fallback to India Gate, New Delhi
  const userLat = geo.latitude ?? 28.6129;
  const userLng = geo.longitude ?? 77.2295;

  const fetchPlaces = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        latitude: String(userLat),
        longitude: String(userLng),
        radius_km: String(radiusKm),
        limit: '50',
        verified_only: String(verifiedOnly),
      });
      if (selectedCategory) params.set('category', selectedCategory);

      const res = await fetch(`http://localhost:8000/api/v1/places/nearby?${params}`);
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const data = await res.json();
      setPlaces(data.places ?? []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load safe places');
    } finally {
      setLoading(false);
    }
  }, [userLat, userLng, radiusKm, selectedCategory, verifiedOnly]);

  useEffect(() => {
    if (!geo.loading) fetchPlaces();
  }, [fetchPlaces, geo.loading]);

  const handlePlaceSelect = useCallback((place: SafePlaceMapItem) => {
    setSelectedPlace(place as Place);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      {/* Header */}
      <div className="px-4 pt-8 pb-4 max-w-7xl mx-auto">
        <div className="flex items-center gap-3 mb-1">
          <div className="w-10 h-10 rounded-xl bg-rose-500/20 flex items-center justify-center">
            <Shield className="w-5 h-5 text-rose-400" />
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-tight">Safe Places Nearby</h1>
            <p className="text-slate-400 text-xs">Verified police stations, hospitals, shelters & helpdesks</p>
          </div>
        </div>

        {/* GPS status badge */}
        <div className="mt-3 flex items-center gap-2 text-xs">
          {geo.loading ? (
            <span className="flex items-center gap-1.5 text-amber-400">
              <Loader2 className="w-3.5 h-3.5 animate-spin" /> Acquiring GPS…
            </span>
          ) : geo.error ? (
            <span className="flex items-center gap-1.5 text-orange-400">
              <WifiOff className="w-3.5 h-3.5" /> GPS unavailable — showing New Delhi
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-emerald-400">
              <Navigation className="w-3.5 h-3.5" />
              Your location ±{geo.accuracy ? Math.round(geo.accuracy) : '?'}m
            </span>
          )}
        </div>
      </div>

      {/* Controls Row */}
      <div className="px-4 pb-4 max-w-7xl mx-auto">
        <div className="bg-slate-800/60 backdrop-blur-sm border border-slate-700/40 rounded-2xl p-4 space-y-3">
          {/* Category Filter Pills */}
          <div className="flex flex-wrap gap-2">
            {CATEGORIES.map((cat) => (
              <button
                key={String(cat.key)}
                onClick={() => setSelectedCategory(cat.key)}
                className={`px-3 py-1.5 rounded-full text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer
                  ${selectedCategory === cat.key
                    ? 'bg-rose-500 text-white shadow-lg shadow-rose-500/30'
                    : 'bg-slate-700/70 text-slate-300 hover:bg-slate-600/80'
                  }`}
              >
                <span>{cat.emoji}</span>
                <span>{cat.label}</span>
              </button>
            ))}
          </div>

          {/* Radius & Verified Filter */}
          <div className="flex flex-wrap gap-4 items-center pt-1">
            <div className="flex items-center gap-2 text-xs text-slate-300">
              <Search className="w-3.5 h-3.5 text-slate-500" />
              <span>Radius:</span>
              {[2, 5, 10, 20].map((r) => (
                <button
                  key={r}
                  onClick={() => setRadiusKm(r)}
                  className={`px-2.5 py-1 rounded-lg font-semibold cursor-pointer transition-all
                    ${radiusKm === r
                      ? 'bg-rose-500 text-white'
                      : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                    }`}
                >
                  {r}km
                </button>
              ))}
            </div>
            <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={verifiedOnly}
                onChange={(e) => setVerifiedOnly(e.target.checked)}
                className="accent-rose-500 w-3.5 h-3.5"
              />
              <Shield className="w-3.5 h-3.5 text-blue-400" />
              Verified only
            </label>
          </div>
        </div>
      </div>

      {/* Main Content: Map + List */}
      <div className="px-4 pb-10 max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-5 gap-4">

        {/* Map Panel */}
        <div
          className="lg:col-span-3 rounded-2xl overflow-hidden border border-slate-700/40"
          style={{ height: '520px' }}
        >
          {places.length > 0 || !loading ? (
            <SafePlacesMap
              places={places}
              userLat={userLat}
              userLng={userLng}
              onPlaceSelect={handlePlaceSelect}
              selectedPlaceId={selectedPlace?.id ?? null}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-slate-800">
              <Loader2 className="w-8 h-8 animate-spin text-rose-400" />
            </div>
          )}
        </div>

        {/* List Panel */}
        <div className="lg:col-span-2 space-y-3 overflow-y-auto" style={{ maxHeight: '520px' }}>
          {error && (
            <div className="p-4 bg-rose-900/40 border border-rose-700/60 rounded-xl text-xs text-rose-300 flex gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-7 h-7 animate-spin text-rose-400" />
            </div>
          ) : places.length === 0 ? (
            <div className="text-center py-16 text-slate-500 text-sm">
              <MapPin className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p>No safe places found within {radiusKm}km.</p>
              <p className="text-xs mt-1">Try increasing the radius or clearing filters.</p>
            </div>
          ) : (
            places.map((place) => <PlaceCard key={place.id} place={place} isSelected={selectedPlace?.id === place.id} onSelect={() => setSelectedPlace(place)} />)
          )}
        </div>
      </div>

      {/* Selected Place Detail Drawer */}
      {selectedPlace && (
        <PlaceDetailDrawer place={selectedPlace} onClose={() => setSelectedPlace(null)} />
      )}
    </div>
  );
};

// ─────────────────────────── Place Card ───────────────────────────────────────
const PlaceCard: React.FC<{ place: Place; isSelected: boolean; onSelect: () => void }> = ({
  place,
  isSelected,
  onSelect,
}) => {
  const cfg = {
    police_station:   { emoji: '🚔', color: 'text-blue-400',   bg: 'bg-blue-500/10' },
    hospital_24_7:    { emoji: '🏥', color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
    women_helpdesk:   { emoji: '💜', color: 'text-purple-400',  bg: 'bg-purple-500/10' },
    pharmacy:         { emoji: '💊', color: 'text-sky-400',     bg: 'bg-sky-500/10' },
    transit_hub:      { emoji: '🚇', color: 'text-amber-400',   bg: 'bg-amber-500/10' },
    verified_shelter: { emoji: '🏠', color: 'text-rose-400',    bg: 'bg-rose-500/10' },
  }[place.category] ?? { emoji: '📍', color: 'text-slate-400', bg: 'bg-slate-500/10' };

  return (
    <button
      onClick={onSelect}
      className={`w-full text-left p-4 rounded-xl border transition-all cursor-pointer
        ${isSelected
          ? 'bg-rose-900/30 border-rose-500/50 shadow-lg shadow-rose-500/10'
          : 'bg-slate-800/60 border-slate-700/40 hover:bg-slate-700/60 hover:border-slate-600/50'
        }`}
    >
      <div className="flex items-start gap-3">
        <div className={`w-9 h-9 rounded-xl ${cfg.bg} flex items-center justify-center shrink-0 text-lg`}>
          {cfg.emoji}
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-bold text-sm text-white truncate">{place.name}</div>
          <div className={`text-xs font-medium ${cfg.color} mt-0.5`}>
            {place.category.replace(/_/g, ' ')}
          </div>

          <div className="flex flex-wrap gap-2 mt-2">
            {place.distance_km != null && (
              <span className="text-[11px] text-slate-400 flex items-center gap-1">
                <Navigation className="w-3 h-3" />
                {place.distance_km.toFixed(2)} km
              </span>
            )}
            {place.safety_score && (
              <span className="text-[11px] text-amber-400 flex items-center gap-1">
                <Star className="w-3 h-3" />
                {place.safety_score.toFixed(1)}
              </span>
            )}
            {place.is_24_7 && (
              <span className="text-[11px] bg-emerald-500/15 text-emerald-400 px-1.5 py-0.5 rounded font-semibold">24/7</span>
            )}
            {place.is_verified && (
              <span className="text-[11px] bg-blue-500/15 text-blue-400 px-1.5 py-0.5 rounded font-semibold flex items-center gap-0.5">
                <CheckCircle2 className="w-2.5 h-2.5" /> Verified
              </span>
            )}
          </div>
        </div>

        {place.phone_number && (
          <a
            href={`tel:${place.phone_number}`}
            onClick={(e) => e.stopPropagation()}
            className="p-2 rounded-lg bg-emerald-600/80 hover:bg-emerald-500 text-white transition-colors shrink-0"
            title={`Call ${place.phone_number}`}
          >
            <Phone className="w-3.5 h-3.5" />
          </a>
        )}
      </div>
    </button>
  );
};

// ─────────────────────────── Place Detail Drawer ──────────────────────────────
const PlaceDetailDrawer: React.FC<{ place: Place; onClose: () => void }> = ({ place, onClose }) => {
  const cfg = {
    police_station:   { emoji: '🚔', label: 'Police Station' },
    hospital_24_7:    { emoji: '🏥', label: 'Hospital (24/7)' },
    women_helpdesk:   { emoji: '💜', label: "Women's Helpdesk" },
    pharmacy:         { emoji: '💊', label: 'Pharmacy' },
    transit_hub:      { emoji: '🚇', label: 'Transit Hub' },
    verified_shelter: { emoji: '🏠', label: 'Verified Shelter' },
  }[place.category] ?? { emoji: '📍', label: place.category };

  const googleMapsUrl = `https://www.google.com/maps/dir/?api=1&destination=${place.latitude},${place.longitude}`;

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 p-4 max-w-xl mx-auto">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden animate-in slide-in-from-bottom">
        <div className="p-5">
          <div className="flex items-start gap-3 mb-4">
            <div className="text-3xl">{cfg.emoji}</div>
            <div className="flex-1">
              <h3 className="font-black text-lg leading-tight">{place.name}</h3>
              <p className="text-slate-400 text-xs mt-0.5">{cfg.label}</p>
            </div>
            <button
              onClick={onClose}
              className="text-slate-500 hover:text-white text-sm font-bold px-2 py-1 rounded-lg hover:bg-slate-800 cursor-pointer"
            >
              ✕
            </button>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs mb-4">
            {place.distance_km != null && (
              <div className="bg-slate-800/80 rounded-xl p-3 text-center">
                <Navigation className="w-4 h-4 mx-auto mb-1 text-rose-400" />
                <p className="font-bold text-white text-base">{place.distance_km.toFixed(2)} km</p>
                <p className="text-slate-500">Distance</p>
              </div>
            )}
            {place.safety_score && (
              <div className="bg-slate-800/80 rounded-xl p-3 text-center">
                <Star className="w-4 h-4 mx-auto mb-1 text-amber-400" />
                <p className="font-bold text-white text-base">{place.safety_score.toFixed(1)} / 5</p>
                <p className="text-slate-500">Safety Score</p>
              </div>
            )}
            <div className="bg-slate-800/80 rounded-xl p-3 text-center">
              <Clock className="w-4 h-4 mx-auto mb-1 text-blue-400" />
              <p className="font-bold text-white">{place.is_24_7 ? '24 / 7' : 'Hours limited'}</p>
              <p className="text-slate-500">{(place as any).operating_hours ?? 'Open hours'}</p>
            </div>
            {place.is_verified && (
              <div className="bg-slate-800/80 rounded-xl p-3 text-center">
                <Shield className="w-4 h-4 mx-auto mb-1 text-emerald-400" />
                <p className="font-bold text-white text-xs leading-tight">{(place as any).verified_by ?? 'Verified'}</p>
                <p className="text-slate-500">Authority</p>
              </div>
            )}
          </div>

          {place.address && (
            <p className="text-slate-400 text-xs mb-4 flex gap-2">
              <MapPin className="w-3.5 h-3.5 shrink-0 mt-0.5 text-slate-500" />
              {place.address}
            </p>
          )}

          <div className="flex gap-3">
            {place.phone_number && (
              <a
                href={`tel:${place.phone_number}`}
                className="flex-1 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl text-sm text-center flex items-center justify-center gap-2 transition-colors"
              >
                <Phone className="w-4 h-4" />
                {place.phone_number}
              </a>
            )}
            <a
              href={googleMapsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl text-sm text-center flex items-center justify-center gap-2 transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
              Directions
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};
