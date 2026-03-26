"""Shared fixtures for flockyou test suite."""
import sys
import os
import threading
import pytest

# Ensure the api directory is on sys.path so flockyou is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import flockyou


@pytest.fixture(autouse=True)
def reset_globals():
    """Reset all mutable global state between tests."""
    flockyou.detections.clear()
    flockyou.cumulative_detections.clear()
    flockyou.gps_history.clear()
    flockyou.gps_data = None
    flockyou.next_detection_id = 1
    flockyou.oui_database.clear()
    flockyou.serial_data_buffer.clear()
    flockyou.serial_connection = None
    flockyou.flock_serial_connection = None
    flockyou.gps_enabled = False
    flockyou.flock_device_connected = False
    flockyou.flock_device_port = None
    flockyou.reconnect_attempts = {'flock': 0, 'gps': 0}
    flockyou.settings = {'gps_port': '', 'flock_port': '', 'filter': 'all'}
    yield


@pytest.fixture()
def client(mocker):
    """Flask test client with socketio.emit mocked out."""
    mocker.patch.object(flockyou.socketio, 'emit', return_value=None)
    mocker.patch('flockyou.save_cumulative_detections', return_value=None)
    flockyou.app.config['TESTING'] = True
    with flockyou.app.test_client() as c:
        yield c
