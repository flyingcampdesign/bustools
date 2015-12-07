# -*- coding: utf-8 -*-

# TODO make serial number print in xxxx-xxxxxx format

import re
import aardvark_py
from array import array

# The Total Phase API doesn't currently support status_string(AA_I2C_STATUS_*)
AA_I2C_STATUS_CODES = {
    aardvark_py.AA_I2C_STATUS_OK: "ok",
    aardvark_py.AA_I2C_STATUS_BUS_ERROR: "a bus error has occurred, transaction was aborted",
    aardvark_py.AA_I2C_STATUS_SLA_ACK: "bus arbitration was lost during master transaction",
    aardvark_py.AA_I2C_STATUS_SLA_NACK: "failed to receive acknowledgment from slave address",
    aardvark_py.AA_I2C_STATUS_DATA_NACK: "last data byte in the transaction was not acknowledged by the slave",
    aardvark_py.AA_I2C_STATUS_ARB_LOST: "lost arbitration to another master on the bus",
    aardvark_py.AA_I2C_STATUS_BUS_LOCKED: "bus has exceeded the bus lock timeout",
    aardvark_py.AA_I2C_STATUS_LAST_DATA_ACK: "master ACKed last byte sent from Aardvark slave"
}

class AardvarkError(Exception):
    """Raised when an Aardvark error occurs."""
    pass

def find_devices():
    """Return a dictionary of all devices attached to this system.

    The dictionary key is the unique ID of the adapter and the dictionary value is the port.
    """
    # find out how many devices are attached
    num_devices, ports, unique_ids = aardvark_py.aa_find_devices_ext(0, 0)
    # get all the available ports and their corresponding unique IDs
    num_devices, ports, unique_ids = aardvark_py.aa_find_devices_ext(num_devices, num_devices)
    devices = {}
    for i in range(len(ports)):
        devices[unique_ids[i]] = ports[i]
    return devices

def print_devices():
    """Print all Aardvark devices attached to this system."""
    devices = sorted(((v,k) for k,v in find_devices().items()))
    if len(devices) > 0:
        print "%d device(s) found:" % len(devices)

        # Print the information on each device
        for port, unique_id in devices:

            # Determine if the device is in-use
            inuse = "(avail)"
            if (port & aardvark_py.AA_PORT_NOT_FREE):
                inuse = "(in-use)"
                port  = port & ~aardvark_py.AA_PORT_NOT_FREE

            # Display device port number, in-use status, and serial number
            print "    port = %d   %s  (%04d-%06d)" % \
                (port, inuse, unique_id / 1000000, unique_id % 1000000)

    else:
        print "No devices found."

def _validate_status(status):
    """Raise an error if the status is not OK."""
    if (status < 0):
        status_string = aardvark_py.aa_status_string(status)
        if status_string:
            raise AardvarkError(status_string)
        elif isinstance(status, int):
            raise ValueError("invalid status code: %d" % status)
        else:
            raise TypeError("invalid status code: %s" % status)

def _aa_i2c_status_string(status):
    """Print the string representation of an Aardvark API I2C status code.

    If status is not found, return None (for consistency with aa_status_string).
    """
    if status in AA_I2C_STATUS_CODES.keys():
        return AA_I2C_STATUS_CODES[status]
    elif isinstance(status, int):
        return None
    else:
        raise TypeError("invalid I2C status code: %s" % status)

def _validate_I2C_status(status):
    """Raise an error if the I2C status is not OK."""
    if (status > 0):
        status_string = _aa_i2c_status_string(status)
        if status_string:
            raise AardvarkError(status_string)
        elif isinstance(status, int):
            raise ValueError("invalid I2C status code: %d" % status)
        else:
            raise TypeError("invalid I2C status code: %s" % status)

def unique_id(serial_number):
    """Translate serial number string into a unique ID."""
    return int(re.sub('[-]', '', serial_number))

def serial_number(unique_id):
    """Translate unique ID into a serial number string."""
    serial_number = str(unique_id)
    return serial_number[:4] + '-' + serial_number[4:]

def version_string(version):
    """Return the string representation of an Aardvark API version"""
    return str((version >> 8) & 0xFF) + '.' + str(version & 0xFF)

def print_version_info(aardvark_version):
    """Print the version info from an AardvarkVersion object"""
    print "Software version: v%s" % version_string(aardvark_version.software)
    print "Firmware version: v%s" % version_string(aardvark_version.firmware)
    print "Hardware version: v%s" % version_string(aardvark_version.hardware)
    print "Software version required by firmware: v%s" % version_string(aardvark_version.sw_req_by_fw)
    print "Firmware version required by software: v%s" % version_string(aardvark_version.fw_req_by_sw)
    print "API version required by software: v%s" % version_string(aardvark_version.api_req_by_sw)

class Aardvark(object):
    """Aardvark is a wrapper class for the Total Phase Aardvark python API.

    Aardvark implements the context management protocol and should be used as a context manager, e.g.

        with Aardvark() as a:
            a.read_register(address, register)
            ...

    This obviates the need to call a.close() explicitly.
    """

    def __init__(self, identifier=0):
        """Return an Aardvark object.

        Attempts to open an Aardvark adapter on initialization based on the identifier argument.  identifier can be either a port number (int or str), unique ID (int or str), or a serial number string.  If no identifier is provided, the default behavior is to open port 0 (if it exists).

        Raise AardvarkError if unable to open an Aardvark adapter.
        """
        self._aardvark_handle = None
        self._open(identifier)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def _open(self, identifier=0):
        """Open Aardvark adapter given the port, unique ID, or serial number.  If no identifier is provided, the default behavior is to open port 0 (if it exists).

        Intended to be called only as part of the constructor initialization, not for existing objects.

        Raise AardvarkError if unable to open an Aardvark adapter.
        """
        devices = find_devices()
        unique_ids = devices.keys()
        ports = devices.values()
        # check if identifier is a serial number string of the form "xxxx-xxxxxx"
        if isinstance(identifier, str) and re.match("(\d{4,4}-\d{6,6})", identifier):
            # convert the serial number to a unique ID
            int_identifier = unique_id(identifier)
        # otherwise, assume it's either a port or a unique ID
        else:
            int_identifier = int(identifier)
        # if the identifier is a serial number
        if int_identifier in unique_ids:
            # get the port that matches the serial number
            port = devices[int_identifier]
        # otherwise check if the identifier is a port
        elif int_identifier in ports:
            # it's a valid port
            port = int_identifier
        # it's not a valid port or unique ID
        else:
            raise AardvarkError("Aardvark adapter %s is not attached" % identifier)
        # check if the port is in use
        if port & aardvark_py.AA_PORT_NOT_FREE:
            port ^= aardvark_py.AA_PORT_NOT_FREE
            raise AardvarkError("port %s in use" % port)
        else:
            self._aardvark_handle = aardvark_py.aa_open(port)
            _validate_status(self._aardvark_handle)
            if self._aardvark_handle <= 0:
                raise AardvarkError("invalid Aardvark handle %s" % self._aardvark_handle)

    def close(self):
        """Close the Aardvark adapter."""
        if self._aardvark_handle:
            num_closed = aardvark_py.aa_close(self._aardvark_handle)
            if not (num_closed == 1):
                raise AardvarkError("closed %d Aardvark adapters, expected to close only %s" % (num_closed, self._aardvark_handle))
            self._aardvark_handle = None

    @property
    def closed(self):
        """bool indicating the current state of the Aardvark adapter. This is a read-only attribute; the close() method changes the value."""
        return not bool(self._aardvark_handle)

    @property
    def version(self):
        """Return AardvarkVersion object containing software, firmware, and hardware version info."""
        # TODO do something more useful with version info instead of just returning the object
        status, version = aardvark_py.aa_version(self._aardvark_handle)
        _validate_status(status)
        return version

    @property
    def port(self):
        """Return the port for this Aardvark adapter."""
        port = aardvark_py.aa_port(self._aardvark_handle)
        _validate_status(port)
        return port

    @property
    def unique_id(self):
        """Return the unique ID for this Aardvark adapter."""
        unique_id = aardvark_py.aa_unique_id(self._aardvark_handle)
        _validate_status(unique_id)
        if unique_id <= 0:
            raise AardvarkError("invalid unique_id: %s" % unique_id)
        return unique_id

    @property
    def serial_number(self):
        """Return the serial number string for this Aardvark adapter."""
        return serial_number(self.unique_id)

    @property
    def i2c_mode(self):
        """Enable or disable I2C mode on the Aardvark adapter.

        True - Enable I2C mode
        False - Disable I2C mode

        If I2C is disabled, the pins can be used as GPIO instead.
        """
        config = aardvark_py.aa_configure(self._aardvark_handle, aardvark_py.AA_CONFIG_QUERY)
        _validate_status(config)
        return bool(config & aardvark_py.AA_CONFIG_I2C_MASK)

    @i2c_mode.setter
    def i2c_mode(self, value):
        if not isinstance(value, bool):
            raise TypeError("invalid I2C mode state: %s (must be boolean)" % value)
        config = aardvark_py.aa_configure(self._aardvark_handle, aardvark_py.AA_CONFIG_QUERY)
        _validate_status(config)
        if value:
            config |= aardvark_py.AA_CONFIG_I2C_MASK
        else:
            config &= ~aardvark_py.AA_CONFIG_I2C_MASK
        current_config = aardvark_py.aa_configure(self._aardvark_handle, config)
        _validate_status(current_config)
        if not (config == current_config):
            raise AardvarkError("unable to configure Aardvark for I2C mode")

    @property
    def spi_mode(self):
        """Enable or disable SPI mode on the Aardvark adapter.

        True - Enable SPI mode
        False - Disable SPI mode

        If SPI is disabled, the pins can be used as GPIO instead.
        """
        config = aardvark_py.aa_configure(self._aardvark_handle, aardvark_py.AA_CONFIG_QUERY)
        _validate_status(config)
        return bool(config & aardvark_py.AA_CONFIG_SPI_MASK)

    @spi_mode.setter
    def spi_mode(self, value):
        if not isinstance(value, bool):
            raise TypeError("invalid SPI mode state: %s (must be boolean)" % value)
        config = aardvark_py.aa_configure(self._aardvark_handle, aardvark_py.AA_CONFIG_QUERY)
        _validate_status(config)
        if value:
            config |= aardvark_py.AA_CONFIG_SPI_MASK
        else:
            config &= ~aardvark_py.AA_CONFIG_SPI_MASK
        current_config = aardvark_py.aa_configure(self._aardvark_handle, config)
        _validate_status(current_config)
        if not (config == current_config):
            raise AardvarkError("unable to configure Aardvark for SPI mode")

    @property
    def target_power(self):
        """Enable or disable target power.

        True - Enable target power
        False - Disable target power
        """
        target_power_status = aardvark_py.aa_target_power(self._aardvark_handle, aardvark_py.AA_TARGET_POWER_QUERY)
        _validate_status(target_power_status)
        return bool(target_power_status & aardvark_py.AA_TARGET_POWER_BOTH)

    @target_power.setter
    def target_power(self, value):
        if not isinstance(value, bool):
            raise TypeError("invalid target power state: %s" % value)
        target_power_status = aardvark_py.aa_target_power(self._aardvark_handle, aardvark_py.AA_TARGET_POWER_QUERY)
        _validate_status(target_power_status)
        if value:
            target_power_status = aardvark_py.AA_TARGET_POWER_BOTH
        else:
            target_power_status = aardvark_py.AA_TARGET_POWER_NONE
        current_target_power_status = aardvark_py.aa_target_power(self._aardvark_handle, target_power_status)
        _validate_status(current_target_power_status)
        if not (target_power_status == current_target_power_status):
            raise AardvarkError("unable to configure Aardvark target power")

    def i2c_free_bus(self):
        """Free the I2C bus."""
        _validate_status(aardvark_py.aa_i2c_free_bus(self._aardvark_handle))

    @property
    def i2c_bitrate(self):
        """Set the I2C bit rate in kHz.

        Maximum bit rate is 800kHz.  Minimum bit rate for I2C master is 1kHz.
        """
        i2c_bitrate = aardvark_py.aa_i2c_bitrate(self._aardvark_handle, 0)
        _validate_status(i2c_bitrate)
        return i2c_bitrate

    @i2c_bitrate.setter
    def i2c_bitrate(self, value):
        if not isinstance(value, int):
            raise TypeError("invalid I2C bitrate value: %s" % value)
        if value > 800:
            raise AardvarkError("unsupported I2C bitrate: %d" % value)
        i2c_bitrate = aardvark_py.aa_i2c_bitrate(self._aardvark_handle, value)
        _validate_status(i2c_bitrate)

    @property
    def i2c_pullup(self):
        """Enable or disable I2C pull-up resistors on the Aardvark adapter.

        True - Enable I2C pull-up resistors
        False - Disable I2C pull-up resistors
        """
        i2c_pullup_status = aardvark_py.aa_i2c_pullup(self._aardvark_handle, aardvark_py.AA_I2C_PULLUP_QUERY)
        _validate_status(i2c_pullup_status)
        return bool(i2c_pullup_status & aardvark_py.AA_I2C_PULLUP_QUERY)

    @i2c_pullup.setter
    def i2c_pullup(self, value):
        if not isinstance(value, bool):
            raise TypeError("invalid I2C pull-up state: %s" % value)
        i2c_pullup_status = aardvark_py.aa_i2c_pullup(self._aardvark_handle, aardvark_py.AA_TARGET_POWER_QUERY)
        _validate_status(i2c_pullup_status)
        if value:
            i2c_pullup_status = aardvark_py.AA_I2C_PULLUP_BOTH
        else:
            i2c_pullup_status = aardvark_py.AA_I2C_PULLUP_NONE
        current_i2c_pullup_status = aardvark_py.aa_i2c_pullup(self._aardvark_handle, i2c_pullup_status)
        _validate_status(current_i2c_pullup_status)
        if not (i2c_pullup_status == current_i2c_pullup_status):
            raise AardvarkError("unable to configure Aardvark I2C pull-ups")

    @property
    def i2c_bus_timeout(self):
        """Set the I2C bus lock timeout in ms."""
        i2c_bus_timeout = aardvark_py.aa_i2c_bus_timeout(self._aardvark_handle, 0)
        _validate_status(i2c_bus_timeout)
        return i2c_bus_timeout

    @i2c_bus_timeout.setter
    def i2c_bus_timeout(self, value):
        if not isinstance(value, int):
            raise TypeError("invalid I2C bus timeout value: %s" % value)
        if value < 10 or value > 450:
            raise AardvarkError("unsupported I2C bus timeout: %d" % value)
        i2c_bus_timeout = aardvark_py.aa_i2c_bus_timeout(self._aardvark_handle, value)
        _validate_status(i2c_bus_timeout)
        if not (i2c_bus_timeout == value):
            raise AardvarkError("unable to configure Aardvark I2C bus timeout")

    def i2c_write(self, address, data):
        """Write an array of bytes to an I2C slave device."""
        # TODO add keywork arguments to enable features provided by I2C flags
        i2c_flags=aardvark_py.AA_I2C_NO_FLAGS
        status, num_written = aardvark_py.aa_i2c_write_ext(self._aardvark_handle, address, i2c_flags, data)
        _validate_I2C_status(status)
        if num_written != len(data):
            raise INA219Error("bytes written (%d) does not match expected (%d)" % (num_written, len(data)))

    def i2c_write_read(self, address, data_out, num_bytes):
        """Atomic write+read an array of bytes to an I2C slave device."""
        # TODO add keywork arguments to enable features provided by I2C flags
        i2c_flags=aardvark_py.AA_I2C_NO_FLAGS
        status, num_written, data_in, num_read = aardvark_py.aa_i2c_write_read(self._aardvark_handle, address, i2c_flags, data_out, num_bytes)
        write_status = status & 0xFF
        read_status = (status >> 8) & 0xFF
        _validate_I2C_status(write_status)
        _validate_I2C_status(read_status)
        if num_written != len(data_out):
            raise INA219Error("bytes written (%d) does not match expected (%d)" % (num_written, len(data_out)))
        if num_read != num_bytes:
            raise INA219Error("bytes read (%d) does not match expected (%d)" % (num_read, num_bytes))
        return data_in
