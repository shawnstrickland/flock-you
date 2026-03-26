"""Tests for lookup_manufacturer()."""
import pytest
import flockyou
from flockyou import lookup_manufacturer


class TestLookupManufacturer:
    def test_known_oui_returns_manufacturer(self):
        flockyou.oui_database['AABBCC'] = 'Acme Corp'
        assert lookup_manufacturer('AA:BB:CC:DD:EE:FF') == 'Acme Corp'

    def test_unknown_oui_returns_unknown_manufacturer(self):
        result = lookup_manufacturer('AA:BB:CC:DD:EE:FF')
        assert result == 'Unknown Manufacturer'

    def test_none_input_returns_none(self):
        assert lookup_manufacturer(None) is None

    def test_empty_string_returns_none(self):
        assert lookup_manufacturer('') is None

    def test_colon_separated_mac(self):
        flockyou.oui_database['AABBCC'] = 'Acme Corp'
        assert lookup_manufacturer('AA:BB:CC:11:22:33') == 'Acme Corp'

    def test_dash_separated_mac(self):
        flockyou.oui_database['AABBCC'] = 'Acme Corp'
        assert lookup_manufacturer('AA-BB-CC-11-22-33') == 'Acme Corp'

    def test_lowercase_mac_normalised(self):
        flockyou.oui_database['AABBCC'] = 'Acme Corp'
        assert lookup_manufacturer('aa:bb:cc:dd:ee:ff') == 'Acme Corp'

    def test_mac_too_short_returns_unknown(self):
        assert lookup_manufacturer('AA:BB') == 'Unknown Manufacturer'
