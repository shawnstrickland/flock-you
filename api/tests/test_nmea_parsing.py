"""Tests for parse_nmea_sentence()."""
import pytest
from flockyou import parse_nmea_sentence


VALID_GGA = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
VALID_GGA_SOUTH_WEST = "$GPGGA,123519,3351.000,S,07046.000,W,1,05,1.2,10.0,M,0.0,M,,*47"
GLONASS_GGA = "$GNGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
NO_FIX_GGA = "$GPGGA,123519,4807.038,N,01131.000,E,0,00,,,M,,M,,*47"


class TestValidSentences:
    def test_basic_gga_returns_dict(self):
        result = parse_nmea_sentence(VALID_GGA)
        assert result is not None
        assert isinstance(result, dict)

    def test_latitude_converted_to_decimal(self):
        result = parse_nmea_sentence(VALID_GGA)
        # 4807.038 N => 48 + 7.038/60 ≈ 48.1173
        assert abs(result['latitude'] - 48.1173) < 0.001

    def test_longitude_converted_to_decimal(self):
        result = parse_nmea_sentence(VALID_GGA)
        # 01131.000 E => 11 + 31.0/60 ≈ 11.5167
        assert abs(result['longitude'] - 11.5167) < 0.001

    def test_south_latitude_is_negative(self):
        result = parse_nmea_sentence(VALID_GGA_SOUTH_WEST)
        assert result['latitude'] < 0

    def test_west_longitude_is_negative(self):
        result = parse_nmea_sentence(VALID_GGA_SOUTH_WEST)
        assert result['longitude'] < 0

    def test_fix_quality_returned(self):
        result = parse_nmea_sentence(VALID_GGA)
        assert result['fix_quality'] == 1

    def test_satellite_count_returned(self):
        result = parse_nmea_sentence(VALID_GGA)
        assert result['satellites'] == 8

    def test_altitude_returned(self):
        result = parse_nmea_sentence(VALID_GGA)
        assert abs(result['altitude'] - 545.4) < 0.01

    def test_glonass_sentence_parsed(self):
        result = parse_nmea_sentence(GLONASS_GGA)
        assert result is not None
        assert result['fix_quality'] == 1

    def test_timestamp_returned(self):
        result = parse_nmea_sentence(VALID_GGA)
        assert result['timestamp'] == '123519'

    def test_precision_up_to_8_decimal_places(self):
        result = parse_nmea_sentence(VALID_GGA)
        # Result should be rounded to 8 decimal places
        assert len(str(result['latitude']).split('.')[-1]) <= 8


class TestNoFixOrMissingData:
    def test_no_fix_returns_none(self):
        assert parse_nmea_sentence(NO_FIX_GGA) is None

    def test_empty_lat_lon_returns_none(self):
        # GGA with empty lat/lon fields
        sentence = "$GPGGA,123519,,N,,E,1,08,0.9,545.4,M,46.9,M,,*47"
        assert parse_nmea_sentence(sentence) is None

    def test_too_few_parts_returns_none(self):
        assert parse_nmea_sentence("$GPGGA,123519,4807.038") is None

    def test_non_gga_sentence_returns_none(self):
        assert parse_nmea_sentence("$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,,,,*1D") is None

    def test_no_dollar_prefix_returns_none(self):
        assert parse_nmea_sentence("GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47") is None

    def test_empty_string_returns_none(self):
        assert parse_nmea_sentence("") is None

    def test_invalid_numeric_values_returns_none(self):
        # Bad altitude field
        sentence = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,NOTANUMBER,M,46.9,M,,*47"
        assert parse_nmea_sentence(sentence) is None
