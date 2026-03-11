import pytest
import pyH2A.Utilities.Unit_handler.Unit_dimension as dim


class TestUnitDimensionHandler:
    """ Test suite for UnitDimensionHandler class """

    def setup_method(self):
        """ Initialize UnitDimensionHandler before each test """
        self.handler = dim.UnitDimensionHandler()

    def test_energy_dimension(self):
        """ Test detection of energy dimension """
        assert self.handler.get_dimension('kWh') == 'energy'
        assert self.handler.get_dimension('J') == 'energy'
        assert self.handler.get_dimension('BTU') == 'energy'

    def test_length_dimension(self):
        """ Test detection of length dimension """
        assert self.handler.get_dimension('m') == 'length'
        assert self.handler.get_dimension('cm') == 'length'
        assert self.handler.get_dimension('ft') == 'length'

    def test_time_dimension(self):
        """ Test detection of time dimension """
        assert self.handler.get_dimension('s') == 'time'
        assert self.handler.get_dimension('min') == 'time'
        assert self.handler.get_dimension('hr') == 'time'

    def test_current_dimension(self):
        """ Test detection of current dimension """
        assert self.handler.get_dimension('A') == 'current'
        assert self.handler.get_dimension('mA') == 'current'

    def test_luminosity_dimension(self):
        """ Test detection of luminosity dimension """
        assert self.handler.get_dimension('cd') == 'luminosity'

    def test_mass_dimension(self):
        """ Test detection of mass dimension """
        assert self.handler.get_dimension('kg') == 'mass'
        assert self.handler.get_dimension('g') == 'mass'
        assert self.handler.get_dimension('lb') == 'mass'

    def test_substance_dimension(self):
        """ Test detection of substance dimension """
        assert self.handler.get_dimension('mol') == 'substance'
        assert self.handler.get_dimension('mmol') == 'substance'

    def test_temperature_dimension(self):
        """ Test detection of temperature dimension """
        assert self.handler.get_dimension('K') == 'temperature'
        assert self.handler.get_dimension('degC') == 'temperature'
        assert self.handler.get_dimension('degF') == 'temperature'
        assert self.handler.get_dimension('degK') == 'temperature'

    def test_delta_temperature_dimension(self):
        """ Test detection of delta temperature dimension """
        assert self.handler.get_dimension('delta_degC') == 'delta_temperature'
        assert self.handler.get_dimension('delta_degF') == 'delta_temperature'
        assert self.handler.get_dimension('delta_degK') == 'delta_temperature'

    def test_volume_dimension(self):
        """ Test detection of volume dimension """
        assert self.handler.get_dimension('l') == 'volume'
        assert self.handler.get_dimension('ml') == 'volume'
        assert self.handler.get_dimension('cc') == 'volume'
        assert self.handler.get_dimension('m3') == 'volume'

    def test_dimensionless(self):
        """ Test detection of dimensionless """
        assert self.handler.get_dimension('rad') == 'dimensionless'
        assert self.handler.get_dimension('') == 'dimensionless'

    def test_currency_dimension(self):
        """ Test detection of currency dimension """
        assert self.handler.get_dimension('USD') == 'currency'


class TestUnitDimensionHandlerInvalidUnits:

    def setup_method(self):
        """ Initialize UnitDimensionHandler before each test """
        self.handler = dim.UnitDimensionHandler()

    def test_invalid_unit(self):
        """ Test handling of invalid unit """
        with pytest.raises(ValueError) as excinfo:
            self.handler.get_dimension('invalid_unit')
        assert "'invalid_unit' is not a valid unit" in str(excinfo.value)


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
