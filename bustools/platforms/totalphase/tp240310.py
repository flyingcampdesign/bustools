# -*- coding: utf-8 -*-

import bustools.devices.pca95xx as pca95xx

# LED states
ON = pca95xx.LOW
OFF = pca95xx.HIGH
LED_STATES = [
    OFF,
    ON
]

class LEDError(Exception):
    pass

def _validate_led_state(led_state):
    """Raise LEDError if the LED state is invalid."""
    if not (led_state in LED_STATES):
        raise LEDError("invalid LED state: %s" % logic_level)

def led_state_string(led_state):
    _validate_led_state(led_state)
    return 'on' if led_state == ON else 'off'

class LED(object):

    def __init__(self, pin, inverted=True, name=None):
        self._pin = pin
        self._pin.direction = pca95xx.OUTPUT
        self.name = name

    def state(self):
        return self._pin.input

    def on(self):
        self._pin.output = ON

    def off(self):
        self._pin.output = OFF

    def toggle(self):
        self._pin.toggle()



class TP240310(object):
    """Total Phase I2C/SPI Activity Board"""

    def __init__(self, i2c_master=None, spi_master=None):

        self.i2c_master = i2c_master
        self.spi_master = spi_master

        if self.i2c_master:

            # I2C GPIO expander
            self.u1 = pca95xx.PCA9554(master=self.i2c_master, address=0x38, name="U1")

            # P0
            self.p0 = self.u1.ports[0].pins[0]
            self.p0.name = "P0"

            # P1
            self.p1 = self.u1.ports[0].pins[1]
            self.p1.name = "P1"

            # P2
            self.p2 = self.u1.ports[0].pins[2]
            self.p2.name = "P2"

            # P3
            self.p3 = self.u1.ports[0].pins[3]
            self.p3.name = "P3"

            # P4
            self.p4 = self.u1.ports[0].pins[4]
            self.p4.name = "P4"

            # P5
            self.p5 = self.u1.ports[0].pins[5]
            self.p5.name = "P5"

            # P6
            self.p6 = self.u1.ports[0].pins[6]
            self.p6.name = "P6"

            # P7
            self.p7 = self.u1.ports[0].pins[7]
            self.p7.name = "P7"

            # Initialize LEDs
            self.d0 = LED(self.p0, "D0")
            self.d1 = LED(self.p1, "D1")
            self.d2 = LED(self.p2, "D2")
            self.d3 = LED(self.p3, "D3")
            self.d4 = LED(self.p4, "D4")
            self.d5 = LED(self.p5, "D5")
            self.d6 = LED(self.p6, "D6")
            self.d7 = LED(self.p7, "D7")

    def _validate_i2c_master(self):
        if not self.i2c_master:
            raise TP240310Error("No I2C master defined")

    def _validate_spi_master(self):
        if not self.spi_master:
            raise AardvarkError("No SPI master defined")
