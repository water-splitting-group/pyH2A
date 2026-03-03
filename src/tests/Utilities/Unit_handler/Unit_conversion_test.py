import pytest
import pyH2A.Utilities.Unit_handler.Unit_conversion as con


class TestUnitConversionHandler:
    """ Test suite for UnitConversionHandler class """

    def setup_method(self):
        """ Initialize UnitConversionHandler before each test """
        self.handler = con.UnitConversionHandler()

    def test_energy_conversion_kWh_to_J(self):
        """ Test conversion from kWh to Joules """
        result = self.handler.convert(1.0, 'kWh')
        expected = 3.6e6 * self.handler.ureg.J
        assert result.magnitude == expected.magnitude
        assert str(result.units) == str(expected.units)

    def test_length_conversion_cm_to_m(self):
        """ Test conversion from centimeters to meters """
        result = self.handler.convert(100.0, 'cm')
        expected = 1.0 * self.handler.ureg.m
        assert result.magnitude == expected.magnitude
        assert str(result.units) == str(expected.units)

    def test_time_conversion_min_to_s(self):
        """ Test conversion from minutes to seconds """
        result = self.handler.convert(60.0, 'min')
        expected = 3600.0 * self.handler.ureg.s
        assert result.magnitude == expected.magnitude
        assert str(result.units) == str(expected.units)

    # add current, luminosity, mass, substance, temperature, volume tests as needed
    def test_mass_conversion_g_to_kg(self):
        """ Test conversion from grams to kilograms """
        result = self.handler.convert(1000.0, 'g')
        expected = 1.0 * self.handler.ureg.kg
        assert result.magnitude == expected.magnitude
        assert str(result.units) == str(expected.units)

    def test_temperature_conversion_C_to_K(self):
        """ Test conversion from Celsius to Kelvin """
        result = self.handler.convert(0.0, 'degC')
        expected = 273.15 * self.handler.ureg.K
        assert result.magnitude == expected.magnitude
        assert str(result.units) == str(expected.units)

    def test_delta_temperature_conversion_F_to_K(self):
        """ Test conversion from delta Fahrenheit to delta Kelvin """
        result = self.handler.convert(1.0, 'delta_degF')
        expected = (5.0 / 9.0) * self.handler.ureg.K
        assert result.magnitude == expected.magnitude
        assert str(result.units) == str(expected.units)

    def test_volume_conversion_ml_to_m3(self):
        """ Test conversion from milliliters to cubic meters """
        result = self.handler.convert(1, 'ml')
        expected = 1E-06 * self.handler.ureg.meter**3
        assert result.magnitude == pytest.approx(expected.magnitude)
        assert str(result.units) == str(expected.units)

    def test_current_conversion_mA_to_A(self):
        """ Test conversion from milliamperes to amperes """
        result = self.handler.convert(1000.0, 'mA')
        expected = 1.0 * self.handler.ureg.A
        assert result.magnitude == expected.magnitude
        assert str(result.units) == str(expected.units)

    def test_substance_conversion_mmol_to_mol(self):
        """ Test conversion from millimoles to moles """
        result = self.handler.convert(1000.0, 'mmol')
        expected = 1.0 * self.handler.ureg.mol
        assert result.magnitude == expected.magnitude
        assert str(result.units) == str(expected.units)

    def test_kilowatt_hour_per_kilogram_to_joule_per_kilogram(self):
        """ Test conversion from kWh/kg to J/kg """
        result = self.handler.convert(1.0, 'kWh/kg')
        expected = 3.6e6 * self.handler.ureg.J / self.handler.ureg.kg
        assert result.magnitude == expected.magnitude
        assert str(result.units) == str(expected.units)

    def test_USD_per_kWh_to_USD_per_J(self):
        """ Test conversion from USD/kWh to USD/J """
        result = self.handler.convert(200, 'USD/kWh')
        expected = (200.0 / 3.6e6) * self.handler.ureg.USD / \
            self.handler.ureg.J
        assert abs(result.magnitude - expected.magnitude) < 1e-6
        assert round(result.magnitude, 4) == round(expected.magnitude, 4)
        assert str(result.units) == str(expected.units)


class TestUnitConversionHandlerInvalidUnits:
    """ Test suite for invalid unit handling in UnitConversionHandler """

    def setup_method(self):
        """ Initialize UnitConversionHandler before each test """
        self.handler = con.UnitConversionHandler()

    def test_invalid_unit_conversion(self):
        """ Test handling of invalid unit """
        with pytest.raises(ValueError) as excinfo:
            self.handler.convert(1.0, 'invalid_unit')
        assert "'invalid_unit' is not defined in the unit registry" in str(
            excinfo.value)


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
