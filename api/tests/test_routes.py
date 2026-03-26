"""Tests for Flask API routes."""
import json
import io
import pytest
import flockyou


SAMPLE_DETECTION = {
    'id': 1,
    'detection_method': 'ble_name',
    'protocol': 'bluetooth_le',
    'mac_address': 'AA:BB:CC:DD:EE:FF',
    'device_name': 'Flock-ABCDEF',
    'rssi': -65,
    'detection_count': 1,
    'alias': '',
}


@pytest.fixture(autouse=True)
def mock_io(mocker):
    mocker.patch('flockyou.save_cumulative_detections', return_value=None)
    mocker.patch.object(flockyou.socketio, 'emit', return_value=None)


class TestGetDetections:
    def test_empty_returns_empty_list(self, client):
        resp = client.get('/api/detections')
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_returns_all_detections(self, client):
        flockyou.detections.append(dict(SAMPLE_DETECTION))
        resp = client.get('/api/detections')
        assert len(resp.get_json()) == 1

    def test_filter_by_detection_method(self, client):
        flockyou.detections.append({**SAMPLE_DETECTION, 'detection_method': 'ble_name'})
        flockyou.detections.append({**SAMPLE_DETECTION, 'mac_address': '11:22:33:44:55:66', 'detection_method': 'mac_prefix'})
        resp = client.get('/api/detections?filter=ble_name')
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]['detection_method'] == 'ble_name'

    def test_cumulative_type_returns_cumulative(self, client):
        flockyou.cumulative_detections.append(dict(SAMPLE_DETECTION))
        resp = client.get('/api/detections?type=cumulative')
        assert len(resp.get_json()) == 1

    def test_session_type_returns_session(self, client):
        flockyou.detections.append(dict(SAMPLE_DETECTION))
        resp = client.get('/api/detections?type=session')
        assert len(resp.get_json()) == 1


class TestGetStats:
    def test_empty_stats(self, client):
        resp = client.get('/api/stats')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['session']['total'] == 0
        assert data['cumulative']['total'] == 0

    def test_wifi_count(self, client):
        flockyou.detections.append({**SAMPLE_DETECTION, 'protocol': 'wifi'})
        resp = client.get('/api/stats')
        assert resp.get_json()['session']['wifi'] == 1

    def test_ble_count(self, client):
        flockyou.detections.append({**SAMPLE_DETECTION, 'protocol': 'bluetooth_le'})
        resp = client.get('/api/stats')
        assert resp.get_json()['session']['ble'] == 1

    def test_gps_count_includes_only_detections_with_gps(self, client):
        flockyou.detections.append({**SAMPLE_DETECTION, 'gps': {'latitude': 40.7}})
        flockyou.detections.append({**SAMPLE_DETECTION, 'mac_address': '11:22:33:44:55:66'})
        resp = client.get('/api/stats')
        assert resp.get_json()['session']['gps'] == 1


class TestClearDetections:
    def test_clears_session_detections(self, client):
        flockyou.detections.append(dict(SAMPLE_DETECTION))
        resp = client.post('/api/clear')
        assert resp.status_code == 200
        assert flockyou.detections == []

    def test_resets_id_counter(self, client):
        flockyou.next_detection_id = 42
        client.post('/api/clear')
        assert flockyou.next_detection_id == 1

    def test_returns_success(self, client):
        resp = client.post('/api/clear')
        assert resp.get_json()['status'] == 'success'


class TestUpdateAlias:
    def test_updates_alias_successfully(self, client):
        flockyou.detections.append(dict(SAMPLE_DETECTION))
        resp = client.post('/api/detection/alias',
                           data=json.dumps({'id': 1, 'alias': 'My Camera'}),
                           content_type='application/json')
        assert resp.status_code == 200
        assert resp.get_json()['status'] == 'success'
        assert flockyou.detections[0]['alias'] == 'My Camera'

    def test_returns_404_for_unknown_id(self, client):
        resp = client.post('/api/detection/alias',
                           data=json.dumps({'id': 99, 'alias': 'x'}),
                           content_type='application/json')
        assert resp.status_code == 404

    def test_returns_400_when_id_missing(self, client):
        resp = client.post('/api/detection/alias',
                           data=json.dumps({'alias': 'x'}),
                           content_type='application/json')
        assert resp.status_code == 400


class TestSettings:
    def test_get_settings_returns_defaults(self, client):
        resp = client.get('/api/settings')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'filter' in data

    def test_post_settings_updates_value(self, client, mocker):
        mocker.patch('flockyou.save_settings', return_value=None)
        resp = client.post('/api/settings',
                           data=json.dumps({'filter': 'ble_name'}),
                           content_type='application/json')
        assert resp.status_code == 200
        assert flockyou.settings['filter'] == 'ble_name'


class TestImportJson:
    def test_import_valid_json(self, client):
        payload = [{'mac': 'AA:BB:CC:DD:EE:FF', 'method': 'ble_name', 'rssi': -60}]
        data = {'file': (io.BytesIO(json.dumps(payload).encode()), 'detections.json')}
        resp = client.post('/api/import/json', data=data, content_type='multipart/form-data')
        assert resp.status_code == 200
        assert resp.get_json()['count'] == 1

    def test_import_single_object_wrapped_in_list(self, client):
        payload = {'mac': 'AA:BB:CC:DD:EE:FF', 'method': 'ble_name', 'rssi': -60}
        data = {'file': (io.BytesIO(json.dumps(payload).encode()), 'det.json')}
        resp = client.post('/api/import/json', data=data, content_type='multipart/form-data')
        assert resp.status_code == 200
        assert resp.get_json()['count'] == 1

    def test_import_invalid_json_returns_400(self, client):
        data = {'file': (io.BytesIO(b'not valid json {{'), 'bad.json')}
        resp = client.post('/api/import/json', data=data, content_type='multipart/form-data')
        assert resp.status_code == 400

    def test_import_no_file_returns_400(self, client):
        resp = client.post('/api/import/json', data={}, content_type='multipart/form-data')
        assert resp.status_code == 400


class TestExportCsv:
    def test_export_empty_detections_returns_400(self, client):
        resp = client.get('/api/export/csv')
        assert resp.status_code == 400

    def test_export_with_detections_returns_file(self, client, tmp_path, mocker):
        mocker.patch('os.makedirs', return_value=None)
        mocker.patch('builtins.open', mocker.mock_open())
        mocker.patch('flockyou.send_file', return_value=flockyou.app.response_class(
            response='csv content', status=200, mimetype='text/csv'))
        flockyou.detections.append(dict(SAMPLE_DETECTION))
        resp = client.get('/api/export/csv')
        assert resp.status_code == 200
