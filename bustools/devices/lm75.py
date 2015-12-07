# -*- coding: utf-8 -*-

import platform
from array import array

class LM75Error(Exception):
    pass

_TEMPERATURE_REGISTER = 0x00
_CONFIGURATION_REGISTER = 0x01
_HYSTERESIS_REGISTER = 0x02
_OVERTEMPERATURE_SHUTDOWN_REGISTER = 0x03

_REGISTER_TYPES = [
    _TEMPERATURE_REGISTER,
    _CONFIGURATION_REGISTER,
    _HYSTERESIS_REGISTER,
    _OVERTEMPERATURE_SHUTDOWN_REGISTER
]

_REGISTER_WIDTH = {
    _TEMPERATURE_REGISTER: 2,
    _CONFIGURATION_REGISTER: 1,
    _HYSTERESIS_REGISTER: 2,
    _OVERTEMPERATURE_SHUTDOWN_REGISTER: 2
}

def _temperature(temperature_register, farenheight=False):
    """Return the temperature in Celsius given the raw temperature register value.

    If farenheight is True, return the temperature in Farenheight.
    """
    temp = (0xFF & (temperature_register >> 8)) + ((0x7 & (temperature_register >> 5)) / 8.0)
    if farenheight:
        temp = (((9 * temp) / 5.0) + 32)
    return temp

def _validate_register_type(register_type):
    """Raise LM75Error if the register is invalid."""
    if not (register_type in _REGISTER_TYPES):
        raise LM75Error("invalid register type: %s" % register_type)

def _read_register(master, address, register):
    """Read a register."""
    _validate_register_type(register)
    data_out = array('B', [0])
    data_out[0] = register
    data_in = master.i2c_write_read(address, data_out, _REGISTER_WIDTH[register])
    value = 0
    if _REGISTER_WIDTH[register] == 1:
        value = data_in[0]
    elif _REGISTER_WIDTH[register] == 2:
        value = ((0xFF & data_in[0]) << 8) + (0xFF & data_in[1])
    return value

def _write_register(master, address, register, value=None):
    """Write a register."""
    _validate_register_type(register)
    data = array('B', [0])
    data[0] = register
    if _REGISTER_WIDTH[register] == 1:
        data.insert(1, 0xFF & value)
    elif _REGISTER_WIDTH[register] == 2:
        data.insert(1, 0xFF & value)
        data.insert(2, 0xFF & (value >> 8))
    else:
        raise LM75Error("invalid register width")
    master.i2c_write(address, data)

class LM75(object):

    def __init__(self, master, address, configuration=0, name=None):

        # I2C master object
        self.master = master

        # I2C slave address
        self.address = address

        # Configuration register value
        self._configuration = configuration

        # name (e.g. reference designator when assembled on a PCB)
        self.name = name

    # --- low level register access ---

    def _read_register(self, register):
        return _read_register(self.master, self.address, register)

    def _write_register(self, register, value=None):
        _write_register(self.master, self.address, register, value)

    # --- register properties ---

    @property
    def _temperature_register(self):
        return self._read_register(_TEMPERATURE_REGISTER)

    @property
    def _configuration_register(self):
        return self._read_register(_CONFIGURATION_REGISTER)

    @_configuration_register.setter
    def _configuration_register(self, value):
        self._write_register(_CONFIGURATION_REGISTER, value)

    @property
    def _hysteresis_register(self):
        return self._read_register(_HYSTERESIS_REGISTER)

    @_hysteresis_register.setter
    def _hysteresis_register(self, value):
        self._write_register(_HYSTERESIS_REGISTER, value)

    @property
    def _overtemperature_shutdown_register(self):
        return self._read_register(_OVERTEMPERATURE_SHUTDOWN_REGISTER)

    @_overtemperature_shutdown_register.setter
    def _overtemperature_shutdown_register(self, value):
        self._write_register(_OVERTEMPERATURE_SHUTDOWN_REGISTER, value)

    def temperature(self, farenheight=False):
        return _temperature(self._temperature_register, farenheight)

    def print_temperature(self, farenheight=False):
        temp = self.temperature(farenheight=farenheight)
        deg = '' if platform.system() in ('Windows', 'Microsoft') else '°'
        if farenheight:
            print "%.2f" % temp + deg + 'F'
        else:
            print "%.2f" % temp + deg + 'C'
