# -*- coding: utf-8 -*-

import math
from array import array

_REGISTER_BYTE_WIDTH = 2
_CONFIGURATION_REGISTER = 0x00
_SHUNT_VOLTAGE_REGISTER = 0x01
_BUS_VOLTAGE_REGISTER = 0x02
_POWER_REGISTER = 0x03
_CURRENT_REGISTER = 0x04
_CALIBRATION_REGISTER = 0x05
_REGISTERS = [
    _CONFIGURATION_REGISTER,
    _SHUNT_VOLTAGE_REGISTER,
    _BUS_VOLTAGE_REGISTER,
    _POWER_REGISTER,
    _CURRENT_REGISTER,
    _CALIBRATION_REGISTER
]

# Shunt voltage register LSB is constant for all PGA settings
# At PGA = 8, 320mV / 2^15 = ~10uV
# At PGA = 4, 160mV / 2^14 = ~10uV
# At PGA = 2,  80mV / 2^13 = ~10uV
# At PGA = 1,  40mV / 2^12 = ~10uV
# _SHUNT_VOLTAGE_REGISTER_LSB = float(0.04) / float(4096)
_SHUNT_VOLTAGE_REGISTER_LSB = 0.00001


# Bus voltage register LSB is constant for all full scale ranges
# At FSR = 32V, 32V / 2^13 = ~40mV
# At FSR = 16V, 16V / 2^12 = ~40mV
# _BUS_VOLTAGE_REGISTER_LSB = float(16) / float(4096)
_BUS_VOLTAGE_REGISTER_LSB = 0.004

# --- helper functions ---

def _validate_register(register):
    """Raise INA219Error if the register is invalid"""
    if not (register in _REGISTERS):
        raise INA219Error("invalid register: %s" % register)

def _raw_bus_voltage_ovf(bus_voltage_register):
    """The Math Overflow Flag (OVF) is set when the power or current calculations are out of range"""
    return bus_voltage_register & 0x1

def _raw_bus_voltage_cnvr(bus_voltage_register):
    """The CNVR bit is set after all conversions, averaging, and multiplications are complete"""
    return (bus_voltage_register >> 1) & 0x1

def _raw_bus_voltage(bus_voltage_register):
    """Extract the raw bus voltage bits from the bus voltage register value"""
    return (bus_voltage_register >> 3) & 0x0FFF

def print_shunt_voltage(shunt_voltage):
    print "Shunt Voltage: {0}V".format(shunt_voltage)

def print_shunt_voltage_mV(shunt_voltage):
    print "Shunt Voltage: {0}mV".format(shunt_voltage * 1000)

def print_current(current):
    print "Current: {0}A".format(current)

def print_current_mA(current):
    print "Current: {0}mA".format(current * 1000)

def print_bus_voltage(bus_voltage):
    print "Bus Voltage: {0}V".format(bus_voltage)

def print_bus_voltage_mV(bus_voltage):
    print "Bus Voltage: {0}mV".format(bus_voltage * 1000)

def print_power(power):
    print "Power: {0}W".format(power)

def print_power_mW(power):
    print "Power: {0}mW".format(power * 1000)

def _pretty_print_registers(address, configuration_register, shunt_voltage_register, bus_voltage_register, power_register, current_register, calibration_register):
    print "----------------------------------------------------"
    print "| INA219 0x{0:02X} Register | Hex    | Binary           |".format(address)
    print "|--------------------------------------------------|"
    print "| Configuration (0x{0:02X}) | 0x{1:04X} | {1:016b} |".format(_CONFIGURATION_REGISTER, configuration_register)
    print "| Shunt Voltage (0x{0:02X}) | 0x{1:04X} | {1:016b} |".format(_SHUNT_VOLTAGE_REGISTER, shunt_voltage_register)
    print "| Bus Voltage   (0x{0:02X}) | 0x{1:04X} | {1:016b} |".format(_BUS_VOLTAGE_REGISTER, bus_voltage_register)
    print "| Power         (0x{0:02X}) | 0x{1:04X} | {1:016b} |".format(_POWER_REGISTER, power_register)
    print "| Current       (0x{0:02X}) | 0x{1:04X} | {1:016b} |".format(_CURRENT_REGISTER, current_register)
    print "| Calibration   (0x{0:02X}) | 0x{1:04X} | {1:016b} |".format(_CALIBRATION_REGISTER, calibration_register)
    print "----------------------------------------------------"

def _pretty_print_configuration(configuration_register):
    rst = (configuration_register >> 15) & 0x1
    d14 = (configuration_register >> 14) & 0x1
    brng = (configuration_register >> 13) & 0x1
    pg1 = (configuration_register >> 12) & 0x1
    pg0 = (configuration_register >> 11) & 0x1
    badc4 = (configuration_register >> 10) & 0x1
    badc3 = (configuration_register >> 9) & 0x1
    badc2 = (configuration_register >> 8) & 0x1
    badc1 = (configuration_register >> 7) & 0x1
    sadc4 = (configuration_register >> 6) & 0x1
    sadc3 = (configuration_register >> 5) & 0x1
    sadc2 = (configuration_register >> 4) & 0x1
    sadc1 = (configuration_register >> 3) & 0x1
    mode3 = (configuration_register >> 2) & 0x1
    mode2 = (configuration_register >> 1) & 0x1
    mode1 = configuration_register & 0x1
    print "--------------------------"
    print "| Configuration Register |"
    print "|------------------------|"
    print "| Bit | Bit Name | Value |"
    print "|------------------------|"
    print "| D15 | RST      | {0:^5} |".format(rst)
    print "| D14 | -        | {0:^5} |".format(d14)
    print "| D13 | BRNG     | {0:^5} |".format(brng)
    print "| D12 | PG1      | {0:^5} |".format(pg1)
    print "| D11 | PG0      | {0:^5} |".format(pg0)
    print "| D10 | BADC4    | {0:^5} |".format(badc4)
    print "| D9  | BADC3    | {0:^5} |".format(badc3)
    print "| D8  | BADC2    | {0:^5} |".format(badc2)
    print "| D7  | BADC1    | {0:^5} |".format(badc1)
    print "| D6  | SADC4    | {0:^5} |".format(sadc4)
    print "| D5  | SADC3    | {0:^5} |".format(sadc3)
    print "| D4  | SADC2    | {0:^5} |".format(sadc2)
    print "| D3  | SADC1    | {0:^5} |".format(sadc1)
    print "| D2  | MODE3    | {0:^5} |".format(mode3)
    print "| D1  | MODE2    | {0:^5} |".format(mode2)
    print "| D0  | MODE1    | {0:^5} |".format(mode1)
    print "--------------------------"

def _pretty_print_bus_voltage(bus_voltage_register):
    ovf = _raw_bus_voltage_ovf(bus_voltage_register)
    cnvr = _raw_bus_voltage_cnvr(bus_voltage_register)
    raw_bus_voltage = _raw_bus_voltage(bus_voltage_register)
    print "------------------------------"
    print "| Bus Voltage Register       |"
    print "|----------------------------|"
    print "| Bit    | Bit Name | Hex    |"
    print "|----------------------------|"
    print "| D3-D15 | BD0-BD12 | 0x{0:04X} |".format(raw_bus_voltage)
    print "| D1     | CNVR     | 0x{0:<4X} |".format(cnvr)
    print "| D0     | OVF      | 0x{0:<4X} |".format(ovf)
    print "------------------------------"

class INA219Error(Exception):
    pass

class INA219(object):

    def __init__(self, master, address, configuration, shunt_resistance, max_expected_current, name=None):

        # reference designator for identification when assembled on a PCB assembly
        self.name = name

        # I2C master object
        self.master = master

        # I2C slave address
        self.address = address

        # value of the configuration register
        self.configuration = configuration

        # value of the shunt resistor in ohms
        self.shunt_resistance = shunt_resistance

        # max expected current through the shunt resistor in amps
        self.max_expected_current = max_expected_current

        # configure & calibrate the device
        self.configure()
        self.calibrate()

    def configure(self):
        self._configuration_register = self.configuration

    def calibrate(self):
        self._calibration_register = self._calculate_calibration()

    def _calculate_calibration(self):
        return math.trunc(0.04096 / float(self._current_register_lsb * self.shunt_resistance))

    # --- low level register access ---

    def _write_register(self, register, value=None):
        _validate_register(register)
        data = array('B', [0])
        data[0] = register
        if value:
            value_msb = (value >> 8) & 0xFF
            value_lsb = value & 0xFF
            data.insert(1, value_msb)
            data.insert(2, value_lsb)
        self.master.i2c_write(self.address, data)

    def _read_register(self, register):
        _validate_register(register)
        data_out = array('B', [0])
        data_out[0] = register
        data_in = self.master.i2c_write_read(self.address, data_out, _REGISTER_BYTE_WIDTH)
        return (data_in[0] << 8) + data_in[1]

    # --- register properties ---

    @property
    def _configuration_register(self):
        return self._read_register(_CONFIGURATION_REGISTER)

    @_configuration_register.setter
    def _configuration_register(self, value):
        self._write_register(_CONFIGURATION_REGISTER, value)

    @property
    def _shunt_voltage_register(self):
        return self._read_register(_SHUNT_VOLTAGE_REGISTER)

    @property
    def _bus_voltage_register(self):
        return self._read_register(_BUS_VOLTAGE_REGISTER)

    @property
    def _power_register(self):
        return self._read_register(_POWER_REGISTER)

    @property
    def _current_register(self):
        return self._read_register(_CURRENT_REGISTER)

    @property
    def _calibration_register(self):
        return self._read_register(_CALIBRATION_REGISTER)

    @_calibration_register.setter
    def _calibration_register(self, value):
        self._write_register(_CALIBRATION_REGISTER, value)

    # --- register LSB properties ---

    @property
    def _shunt_voltage_register_lsb(self):
        return _SHUNT_VOLTAGE_REGISTER_LSB

    @property
    def _bus_voltage_register_lsb(self):
        return _BUS_VOLTAGE_REGISTER_LSB

    @property
    def _current_register_lsb(self):
        return self.max_expected_current / float(32767)

    @property
    def _power_register_lsb(self):
        return 20 * self._current_register_lsb

    # --- normalized results ---

    def shunt_voltage(self):
        """Shunt voltage in volts"""
        return self._shunt_voltage_register * self._shunt_voltage_register_lsb

    def bus_voltage(self):
        """Bus voltage in volts"""
        return _raw_bus_voltage(self._bus_voltage_register) * self._bus_voltage_register_lsb

    def bus_voltage_ext(self):
        """Bus voltage in volts, OVF, CNVR"""
        bus_voltage_register = self._bus_voltage_register
        return _raw_bus_voltage(bus_voltage_register) * self._bus_voltage_register_lsb, bool(_raw_bus_voltage_ovf(bus_voltage_register)), bool(_raw_bus_voltage_cnvr(bus_voltage_register))

    def power(self):
        """Power in watts"""
        return self._power_register * self._power_register_lsb

    def current(self):
        """Current in amps"""
        return self._current_register * self._current_register_lsb

    # --- debugging helper methods ---

    def _dump_registers(self):
        _pretty_print_registers(self.address, self._configuration_register, self._shunt_voltage_register, self._bus_voltage_register, self._power_register, self._current_register, self._calibration_register)

    def _dump_configuration_register(self):
        _pretty_print_configuration(self._configuration_register)

    def _dump_bus_voltage_register(self):
        _pretty_print_bus_voltage(self._bus_voltage_register)
