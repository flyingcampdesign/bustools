# -*- coding: utf-8 -*-

from array import array

_INPUT_REGISTER = 0x00
_OUTPUT_REGISTER = 0x01
_POLARITY_REGISTER = 0x02
_CONFIGURATION_REGISTER = 0x03
_REGISTER_TYPES = [
    _INPUT_REGISTER,
    _OUTPUT_REGISTER,
    _POLARITY_REGISTER,
    _CONFIGURATION_REGISTER
]
_REGISTER_BYTE_WIDTH = 1

LOW = 0
HIGH = 1
LOGIC_LEVELS = [
    LOW,
    HIGH
]

OUTPUT = 0
INPUT = 1
DIRECTIONS =[
    OUTPUT,
    INPUT
]

DEFAULT = 0
INVERTED = 1
POLARITIES = [
    DEFAULT,
    INVERTED
]

class PCA95xxError(Exception):
    pass

def _validate_logic_level(logic_level):
    """Raise PCA95xxError if the logic level is invalid."""
    if not (logic_level in LOGIC_LEVELS):
        raise PCA95xxError("invalid logic level: %s" % logic_level)

def logic_level_string(logic_level):
    _validate_logic_level(logic_level)
    return 'high' if logic_level == HIGH else 'low'

def _validate_direction(direction):
    """Raise PCA95xxError if the direction is invalid."""
    if not (direction in DIRECTIONS):
        raise PCA95xxError("invalid direction: %s" % direction)

def direction_string(direction):
    _validate_direction(direction)
    return 'input' if direction == INPUT else 'output'

def _validate_polarity(polarity):
    """Raise PCA95xxError if the polarity is invalid."""
    if not (polarity in POLARITIES):
        raise PCA95xxError("invalid polarity: %s" % polarity)

def polarity_string(polarity):
    _validate_polarity(polarity)
    return 'inverted' if polarity == INVERTED else 'default'

def _command(register_offset, port_number, register_type):
    """Return the command register value corresponding to the register type for a given port number and register offset."""
    return (register_offset * register_type) + port_number

def _validate_register_type(register_type):
    """Raise PCA95xxError if the register is invalid."""
    if not (register_type in _REGISTER_TYPES):
        raise PCA95xxError("invalid register type: %s" % register_type)

def _read_register(master, address, register_offset, port_number, register_type):
    """Read a register corresponding to the register type for a given port number and register offset."""
    _validate_register_type(register_type)
    data_out = array('B', [0])
    data_out[0] = _command(register_offset, port_number, register_type)
    data_in = master.i2c_write_read(address, data_out, 1)
    return data_in[0]

def _write_register(master, address, register_offset, port_number, register_type, value=None):
    """Write a register corresponding to the register type for a given port number and register offset."""
    _validate_register_type(register_type)
    data = array('B', [0])
    data[0] = _command(register_offset, port_number, register_type)
    if value:
        data.insert(1, value)
    master.i2c_write(address, data)

def test_bit(int_type, offset):
    """Return HIGH if the bit at 'offset' is one, otherwise return LOW."""
    mask = 1 << offset
    return int_type & mask

def set_bit(int_type, offset):
    """Return an integer with the bit at 'offset' set to 1."""
    mask = 1 << offset
    return int_type | mask

def clear_bit(int_type, offset):
    """Return an integer with the bit at 'offset' cleared."""
    mask = ~(1 << offset)
    return int_type & mask

def toggle_bit(int_type, offset):
    """Return an integer with the bit at 'offset' inverted, 0 -> 1 and 1 -> 0."""
    mask = 1 << offset
    return int_type ^ mask

class GPIO(object):

    def __init__(self, port, number, name=None):
        self._port = port
        self.number = number
        self._name = name

    @property
    def name(self):
        if self._name:
            return self._name
        else:
            return "%s.%s.%s" % (self._port._expander.name, self._port.number, self.number)

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def port_number(self):
        return self._port.number

    @property
    def input(self):
        return HIGH if test_bit(self._port._input_register, self.number) else LOW

    @property
    def output(self):
        return HIGH if test_bit(self._port._output_register, self.number) else LOW

    @output.setter
    def output(self, value):
        _validate_logic_level(value)
        register = self._port._output_register
        if value == HIGH:
            self._port._output_register = set_bit(register, self.number)
        else:
            self._port._output_register = clear_bit(register, self.number)

    @property
    def polarity(self):
        return INVERTED if test_bit(self._port._polarity_register, self.number) else DEFAULT

    @polarity.setter
    def polarity(self, value):
        _validate_polarity(value)
        register = self._port._polarity_register
        if value == INVERTED:
            self._port._polarity_register = set_bit(register, self.number)
        else:
            self._port._polarity_register = clear_bit(register, self.number)

    @property
    def direction(self):
        return INPUT if test_bit(self._port._configuration_register, self.number) else OUTPUT

    @direction.setter
    def direction(self, value):
        _validate_direction(value)
        register = self._port._configuration_register
        if value == INPUT:
            self._port._configuration_register = set_bit(register, self.number)
        else:
            self._port._configuration_register = clear_bit(register, self.number)

    def toggle(self):
        self._port._output_register = toggle_bit(self._port._output_register, self.number)

class Port(object):

    def __init__(self, expander, width, number):
        self._expander = expander
        self.number = number

        # initialize pins
        self.pins = []
        for pin_number in range(width):
            self.pins.append(GPIO(self, pin_number))

    # --- register properties ---

    @property
    def _input_register(self):
        return self._expander._read_register(self.number, _INPUT_REGISTER)

    @property
    def _output_register(self):
        return self._expander._read_register(self.number, _OUTPUT_REGISTER)

    @_output_register.setter
    def _output_register(self, value):
        self._expander._write_register(self.number, _OUTPUT_REGISTER, value)

    @property
    def _polarity_register(self):
        return self._expander._read_register(self.number, _POLARITY_REGISTER)

    @_polarity_register.setter
    def _polarity_register(self, value):
        self._expander._write_register(self.number, _POLARITY_REGISTER, value)

    @property
    def _configuration_register(self):
        return self._expander._read_register(self.number, _CONFIGURATION_REGISTER)

    @_configuration_register.setter
    def _configuration_register(self, value):
        self._expander._write_register(self.number, _CONFIGURATION_REGISTER, value)

class PCA95XX(object):

    def __init__(self, master, address, register_offset, ports, width, name=None):

        # I2C master object
        self.master = master

        # I2C slave address
        self.address = address

        # offset between registers corresponding to the same port, i.e.
        # if polarity inversion port 0 = 0x04 and configuration port 0 = 0x06,
        # then register_offset = 0x06 - 0x04 = 0x02
        self._register_offset = register_offset

        # name (e.g. reference designator when assembled on a PCB)
        self.name = name

        # initialize ports
        self.ports = []
        for number in range(ports):
            self.ports.append(Port(expander=self, width=width, number=number))

    # --- low level register access ---

    def _read_register(self, port_number, register_type):
        return _read_register(self.master, self.address, self._register_offset, port_number, register_type)

    def _write_register(self, port_number, register_type, value=None):
        _write_register(self.master, self.address, self._register_offset, port_number, register_type, value)

class PCA9536(PCA95XX):

    def __init__(self, master, address, name=None):
        PCA95XX.__init__(self, master=master, address=address, register_offset=1, ports=1, width=4, name=name)

class PCA9554(PCA95XX):

    def __init__(self, master, address, name=None):
        PCA95XX.__init__(self, master=master, address=address, register_offset=1, ports=1, width=8, name=name)

class PCA9557(PCA95XX):

    def __init__(self, master, address, name=None):
        PCA95XX.__init__(self, master=master, address=address, register_offset=1, ports=1, width=8, name=name)

class PCA9555(PCA95XX):

    def __init__(self, master, address, name=None):
        PCA95XX.__init__(self, master=master, address=address, register_offset=2, ports=2, width=8, name=name)

class PCA9505(PCA95XX):

    def __init__(self, master, address, name=None):
        PCA95XX.__init__(self, master=master, address=address, register_offset=8, ports=5, width=8, name=name)
