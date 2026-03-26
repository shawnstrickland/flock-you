"""Tests for validate_gps_data() and find_best_gps_match()."""
import time
import pytest
import flockyou
from flockyou import validate_gps_data, find_best_gps_match


VALID_GPS = {
    'latitude': 40.7128,
    'longitude': -74.0060,
    'fix_quality': 1,
    'satellites': 8,
    'altitude': 10.0,
}


class TestValidateGpsData:
    def test_valid_data_returns_true(self):
        ok, msg = validate_gps_data(VALID_GPS)
        assert ok is True

    def test_none_input_returns_false(self):
        ok, msg = validate_gps_data(None)
        assert ok is False

    def test_missing_latitude_returns_false(self):
        ok, msg = validate_gps_data({'longitude': -74.0, 'fix_quality': 1})
        assert ok is False

    def test_missing_longitude_returns_false(self):
        ok, msg = validate_gps_data({'latitude': 40.7, 'fix_quality': 1})
        assert ok is False

    def test_latitude_too_high_returns_false(self):
        ok, msg = validate_gps_data({**VALID_GPS, 'latitude': 91})
        assert ok is False

    def test_latitude_too_low_returns_false(self):
        ok, msg = validate_gps_data({**VALID_GPS, 'latitude': -91})
        assert ok is False

    def test_longitude_too_high_returns_false(self):
        ok, msg = validate_gps_data({**VALID_GPS, 'longitude': 181})
        assert ok is False

    def test_longitude_too_low_returns_false(self):
        ok, msg = validate_gps_data({**VALID_GPS, 'longitude': -181})
        assert ok is False

    def test_poor_fix_quality_returns_false(self):
        ok, msg = validate_gps_data({**VALID_GPS, 'fix_quality': 0})
        assert ok is False

    def test_boundary_coordinates_are_valid(self):
        ok, _ = validate_gps_data({**VALID_GPS, 'latitude': 90, 'longitude': 180})
        assert ok is True
        ok, _ = validate_gps_data({**VALID_GPS, 'latitude': -90, 'longitude': -180})
        assert ok is True


class TestFindBestGpsMatch:
    def _make_entry(self, system_time, fix_quality=1, lat=40.7128, lon=-74.006):
        return {
            'latitude': lat,
            'longitude': lon,
            'fix_quality': fix_quality,
            'system_timestamp': system_time,
            'timestamp': '123519',
        }

    def test_empty_history_returns_none(self):
        assert find_best_gps_match(time.time()) is None

    def test_returns_matching_entry_within_threshold(self):
        now = time.time()
        entry = self._make_entry(now)
        flockyou.gps_history.append(entry)
        result = find_best_gps_match(now)
        assert result is not None
        assert result['latitude'] == 40.7128

    def test_no_match_when_all_entries_outside_threshold(self):
        old_time = time.time() - 60  # 60s ago, beyond the 30s threshold
        flockyou.gps_history.append(self._make_entry(old_time))
        result = find_best_gps_match(time.time())
        assert result is None

    def test_returns_closest_entry_when_multiple_candidates(self):
        now = time.time()
        close_entry = self._make_entry(now - 2, lat=1.0)
        far_entry = self._make_entry(now - 20, lat=2.0)
        flockyou.gps_history.extend([far_entry, close_entry])
        result = find_best_gps_match(now)
        assert result['latitude'] == 1.0  # closer entry wins

    def test_accepts_iso_format_timestamp(self):
        now = time.time()
        from datetime import datetime
        iso_ts = datetime.fromtimestamp(now).isoformat()
        flockyou.gps_history.append(self._make_entry(now))
        result = find_best_gps_match(iso_ts)
        assert result is not None

    def test_accepts_display_format_timestamp(self):
        now = time.time()
        from datetime import datetime
        display_ts = datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')
        flockyou.gps_history.append(self._make_entry(now))
        result = find_best_gps_match(display_ts)
        assert result is not None

    def test_at_threshold_boundary_returns_match(self):
        now = time.time()
        # Exactly at the 30s threshold should still match
        entry = self._make_entry(now - 30)
        flockyou.gps_history.append(entry)
        result = find_best_gps_match(now)
        assert result is not None
