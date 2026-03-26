"""Tests for add_detection_from_serial()."""
import time
import pytest
from unittest.mock import patch
import flockyou
from flockyou import add_detection_from_serial


SAMPLE_DETECTION = {
    'detection_method': 'ble_name',
    'protocol': 'bluetooth_le',
    'mac_address': 'AA:BB:CC:DD:EE:FF',
    'device_name': 'Flock-ABCDEF',
    'rssi': -65,
}

GPS_ENTRY = {
    'latitude': 40.7128,
    'longitude': -74.0060,
    'altitude': 10.0,
    'fix_quality': 1,
    'satellites': 8,
    'timestamp': '123519',
    'system_timestamp': time.time(),
    'hdop': 0.9,
}


@pytest.fixture(autouse=True)
def mock_io(mocker):
    mocker.patch('flockyou.save_cumulative_detections', return_value=None)
    mocker.patch.object(flockyou.socketio, 'emit', return_value=None)


class TestNewDetection:
    def test_detection_added_to_list(self):
        add_detection_from_serial(dict(SAMPLE_DETECTION))
        assert len(flockyou.detections) == 1

    def test_detection_assigned_id(self):
        add_detection_from_serial(dict(SAMPLE_DETECTION))
        assert flockyou.detections[0]['id'] == 1

    def test_ids_increment_for_multiple_detections(self):
        add_detection_from_serial(dict(SAMPLE_DETECTION))
        d2 = {**SAMPLE_DETECTION, 'mac_address': '11:22:33:44:55:66'}
        add_detection_from_serial(d2)
        assert flockyou.detections[0]['id'] == 1
        assert flockyou.detections[1]['id'] == 2

    def test_detection_count_starts_at_one(self):
        add_detection_from_serial(dict(SAMPLE_DETECTION))
        assert flockyou.detections[0]['detection_count'] == 1

    def test_detection_added_to_cumulative(self):
        add_detection_from_serial(dict(SAMPLE_DETECTION))
        assert len(flockyou.cumulative_detections) == 1

    def test_alias_initialised_to_empty_string(self):
        add_detection_from_serial(dict(SAMPLE_DETECTION))
        assert flockyou.detections[0]['alias'] == ''

    def test_manufacturer_populated(self):
        flockyou.oui_database['AABBCC'] = 'Acme Corp'
        add_detection_from_serial(dict(SAMPLE_DETECTION))
        assert flockyou.detections[0].get('manufacturer') == 'Acme Corp'

    def test_server_timestamp_added(self):
        add_detection_from_serial(dict(SAMPLE_DETECTION))
        assert 'server_timestamp' in flockyou.detections[0]

    def test_new_detection_socket_emit_called(self, mocker):
        spy = mocker.patch.object(flockyou.socketio, 'emit')
        add_detection_from_serial(dict(SAMPLE_DETECTION))
        spy.assert_called_once_with('new_detection', flockyou.detections[0])


class TestDuplicateDetection:
    def test_duplicate_mac_not_added_again(self):
        add_detection_from_serial(dict(SAMPLE_DETECTION))
        add_detection_from_serial(dict(SAMPLE_DETECTION))
        assert len(flockyou.detections) == 1

    def test_duplicate_mac_increments_count(self):
        add_detection_from_serial(dict(SAMPLE_DETECTION))
        add_detection_from_serial(dict(SAMPLE_DETECTION))
        assert flockyou.detections[0]['detection_count'] == 2

    def test_update_emits_detection_updated(self, mocker):
        spy = mocker.patch.object(flockyou.socketio, 'emit')
        add_detection_from_serial(dict(SAMPLE_DETECTION))
        spy.reset_mock()
        add_detection_from_serial(dict(SAMPLE_DETECTION))
        assert spy.call_args[0][0] == 'detection_updated'

    def test_last_seen_updated_on_duplicate(self):
        add_detection_from_serial(dict(SAMPLE_DETECTION))
        first_seen = flockyou.detections[0].get('first_seen')
        add_detection_from_serial(dict(SAMPLE_DETECTION))
        assert flockyou.detections[0].get('first_seen') == first_seen  # unchanged
        assert 'last_seen' in flockyou.detections[0]


class TestGpsAssignment:
    def test_gps_attached_from_temporal_match(self, mocker):
        now = time.time()
        entry = {**GPS_ENTRY, 'system_timestamp': now}
        flockyou.gps_history.append(entry)
        mocker.patch('flockyou.find_best_gps_match', return_value=entry)
        add_detection_from_serial(dict(SAMPLE_DETECTION))
        assert flockyou.detections[0].get('gps') is not None
        assert flockyou.detections[0]['gps']['latitude'] == 40.7128

    def test_gps_falls_back_to_current_when_no_history(self):
        flockyou.gps_data = {**GPS_ENTRY, 'system_timestamp': time.time()}
        add_detection_from_serial(dict(SAMPLE_DETECTION))
        assert flockyou.detections[0].get('gps') is not None

    def test_no_gps_attached_when_none_available(self):
        flockyou.gps_data = None
        add_detection_from_serial(dict(SAMPLE_DETECTION))
        assert flockyou.detections[0].get('gps') is None
