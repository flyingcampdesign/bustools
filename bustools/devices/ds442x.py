# -*- coding: utf-8 -*-

from array import array

_OUT0 = 0xF8
_OUT1 = 0xF9
_OUT2 = 0xFA
_OUT3 = 0xFB
_REGISTERS = [
    _OUT0,
    _OUT1,
    _OUT2,
    _OUT3
]

_SINK = 0
_SOURCE = 1

class DS442xError(Exception):
    pass

def _validate_register(register):
    """Raise DS442xError if the register is invalid."""
    if not (register in _REGISTERS):
        raise DS442xError("invalid register: %s" % register)

def _read_register(i2c_master, i2c_address, register):
    """Read a register value."""
    _validate_register(register)
    data_out = array('B', [register])
    # _write_register(i2c_master, i2c_address, register)
    # data_in = i2c_master.i2c_read(i2c_address, 1)
    data_in = i2c_master.i2c_write_read(i2c_address, data_out, 1)
    return data_in[0]

def _write_register(i2c_master, i2c_address, register, value=None):
    """Write a register value."""
    _validate_register(register)
    data = array('B', [register])
    if value is not None:
        data.insert(1, value & 0xFF)
    i2c_master.i2c_write(i2c_address, data)

class Channel(object):

    def __init__(self, dac, number, r_fs, name=None):
        self._dac = dac
        self.number = number
        self.r_fs = r_fs
        self._name = name

    @property
    def name(self):
        if self._name:
            return self._name
        else:
            return "OUT%s" % self.number

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def output_control_register(self):
        return self._dac._read_register(_REGISTERS[self.number])

    @output_control_register.setter
    def output_control_register(self, value):
        self._dac._write_register(_REGISTERS[self.number], value)

    def initialize(self):
        self.output_control_register = 0

class DS442x(object):

    def __init__(self, i2c_master, i2c_address, channels, r_fs0=None, r_fs1=None, r_fs2=None, r_fs3=None, name=None):

        # I2C master object
        self.i2c_master = i2c_master

        # I2C slave address
        self.i2c_address = i2c_address

        # Number of current sink/source channels
        if channels in [2,4]:
            self._channels = channels
        else:
            raise DS442xError("invalid number of channels: %s" % channels)

        # name (e.g. reference designator when assembled on a PCB)
        self.name = name

        # initialize full-scale calibration resistors
        self._fs_cal_resistors = [
            r_fs0,
            r_fs1,
            r_fs2,
            r_fs3
        ]

        # initialize channels
        self.channels = []
        for channel in range(channels):
            self.channels.append(Channel(dac=self, number=channel, r_fs=self._fs_cal_resistors[channel]))

    # --- low level register access ---

    def _read_register(self, register):
        return _read_register(self.i2c_master, self.i2c_address, register)

    def _write_register(self, register, value=None):
        _write_register(self.i2c_master, self.i2c_address, register, value)

class DS4422(DS442x):

    def __init__(self, i2c_master, i2c_address, r_fs0=None, r_fs1=None, r_fs2=None, r_fs3=None, name=None):
        DS442x.__init__(self, i2c_master=i2c_master, i2c_address=i2c_address, channels=2, r_fs0=r_fs0, r_fs1=r_fs1, r_fs2=r_fs2, r_fs3=r_fs3, name=name)

class DS4424(DS442x):

    def __init__(self, i2c_master, i2c_address, r_fs0=None, r_fs1=None, r_fs2=None, r_fs3=None, name=None):
        DS442x.__init__(self, i2c_master=i2c_master, i2c_address=i2c_address, channels=4, r_fs0=r_fs0, r_fs1=r_fs1, r_fs2=r_fs2, r_fs3=r_fs3, name=name)
