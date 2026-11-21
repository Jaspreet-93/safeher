"""Unit tests for Haversine distance calculations and bounding box utility."""
import math

import pytest

from app.services.place_service import bounding_box, haversine_distance


class TestHaversineDistance:
    def test_zero_distance_same_point(self):
        dist = haversine_distance(28.6139, 77.2090, 28.6139, 77.2090)
        assert dist == pytest.approx(0.0, abs=1e-6)

    def test_known_delhi_to_connaught_place(self):
        # India Gate to Connaught Place — roughly 2.6 km
        dist = haversine_distance(28.6129, 77.2295, 28.6315, 77.2167)
        assert 2.0 <= dist <= 3.5, f"Expected ~2.6km, got {dist:.3f} km"

    def test_delhi_to_bengaluru(self):
        # Delhi to Bengaluru — roughly 1740 km
        dist = haversine_distance(28.6139, 77.2090, 12.9716, 77.5946)
        assert 1700.0 <= dist <= 1800.0, f"Expected ~1740 km, got {dist:.1f} km"

    def test_equatorial_symmetry(self):
        # Swapping source and destination should give same distance
        dist_ab = haversine_distance(28.0, 77.0, 29.0, 78.0)
        dist_ba = haversine_distance(29.0, 78.0, 28.0, 77.0)
        assert dist_ab == pytest.approx(dist_ba, rel=1e-9)

    def test_meridian_crossing(self):
        # 1° of latitude ≈ 111 km; 1° near equator should give ~111 km
        dist = haversine_distance(0.0, 0.0, 1.0, 0.0)
        assert 110.5 <= dist <= 111.5

    def test_distance_is_always_non_negative(self):
        for lat1, lng1, lat2, lng2 in [
            (-33.87, 151.21, 51.51, -0.13),  # Sydney to London
            (40.71, -74.01, 35.68, 139.69),  # New York to Tokyo
            (0.0, 0.0, 0.0, 180.0),           # Opposite longitudes at equator
        ]:
            assert haversine_distance(lat1, lng1, lat2, lng2) >= 0.0


class TestBoundingBox:
    def test_bounding_box_contains_origin(self):
        lat, lng = 28.6139, 77.2090
        min_lat, max_lat, min_lng, max_lng = bounding_box(lat, lng, 5.0)
        assert min_lat < lat < max_lat
        assert min_lng < lng < max_lng

    def test_bounding_box_radius_1km(self):
        lat, lng = 0.0, 0.0
        min_lat, max_lat, min_lng, max_lng = bounding_box(lat, lng, 1.0)
        # At equator: 1km ≈ 1/111 degrees in both dimensions
        expected_delta = 1.0 / 111.0
        assert math.fabs((max_lat - min_lat) / 2 - expected_delta) < 0.001
        assert math.fabs((max_lng - min_lng) / 2 - expected_delta) < 0.001

    def test_bounding_box_at_high_latitude(self):
        # At latitude 60°, longitude degrees compress by cos(60°) = 0.5
        min_lat, max_lat, min_lng, max_lng = bounding_box(60.0, 30.0, 10.0)
        lat_span = (max_lat - min_lat) / 2
        lng_span = (max_lng - min_lng) / 2
        # Longitude span should be ~2x latitude span at 60° latitude
        assert lng_span > lat_span, "Longitude span should be wider at high latitude"
