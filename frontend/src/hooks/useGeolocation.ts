import { useState, useEffect } from 'react';

export interface GeoLocationState {
  latitude: number | null;
  longitude: number | null;
  accuracy: number | null;
  timestamp: number | null;
  error: string | null;
  loading: boolean;
}

export const useGeolocation = (enabled: boolean = true) => {
  const [location, setLocation] = useState<GeoLocationState>({
    latitude: null,
    longitude: null,
    accuracy: null,
    timestamp: null,
    error: null,
    loading: enabled,
  });

  useEffect(() => {
    if (!enabled) return;

    if (!navigator.geolocation) {
      setLocation((prev) => ({
        ...prev,
        error: 'Geolocation is not supported by your browser.',
        loading: false,
      }));
      return;
    }

    const handleSuccess = (position: GeolocationPosition) => {
      setLocation({
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
        timestamp: position.timestamp,
        error: null,
        loading: false,
      });
    };

    const handleError = (error: GeolocationPositionError) => {
      let errorMsg = 'Failed to retrieve location.';
      switch (error.code) {
        case error.PERMISSION_DENIED:
          errorMsg = 'Location permission was denied. Please enable GPS permissions.';
          break;
        case error.POSITION_UNAVAILABLE:
          errorMsg = 'Location information is currently unavailable.';
          break;
        case error.TIMEOUT:
          errorMsg = 'Location request timed out.';
          break;
      }
      setLocation((prev) => ({
        ...prev,
        error: errorMsg,
        loading: false,
      }));
    };

    const options: PositionOptions = {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 15000,
    };

    navigator.geolocation.getCurrentPosition(handleSuccess, handleError, options);

    const watchId = navigator.geolocation.watchPosition(handleSuccess, handleError, options);

    return () => navigator.geolocation.clearWatch(watchId);
  }, [enabled]);

  return location;
};
