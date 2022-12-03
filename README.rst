**Note:** This package is no longer being developed. It is recommended to use `Adafruit-Blinka <https://github.com/adafruit/Adafruit_Blinka>`_ instead.

bustools
========

Python tools for electrical busses such as I2C and SPI.

Status
------

There is currently basic support for the `Total Phase Aardvark <http://www.totalphase.com/products/aardvark-i2cspi/>`_ adapter as an I2C master.  There is also initial support for a couple I2C slave devices (see `bustools/devices/`) and the `I2C/SPI Activity Board <http://www.totalphase.com/products/activity-board/>`_ platform.

The public API is not guaranteed to be stable until 1.x release.


Installation
------------

The ``bustools`` package can be installed from PyPI using ``pip``:

.. code-block:: console

    $ pip install bustools

Support for the Total Phase Aardvark adapter is not included by default since it only supports Windows, Mac OS X, and Linux.  To include support for the Aardvark adapter, you need to specify the 'aardvark' extra:

.. code-block:: console

    $ pip install bustools[aardvark]


Usage
-----

TODO


Examples
--------

The following example uses the `Total Phase Aardvark <http://www.totalphase.com/products/aardvark-i2cspi/>`_ adapter to turn on LED `D0` on the `I2C/SPI Activity Board <http://www.totalphase.com/products/activity-board/>`_.

.. code-block:: console

    $ python
    Python 2.7.10 (default, Dec  3 2015, 13:28:10)
    [GCC 4.2.1 Compatible Apple LLVM 7.0.0 (clang-700.1.76)] on darwin
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import bustools.platforms.totalphase.tp240310 as tp240310
    >>> import bustools.adapters.aardvark as aardvark
    >>> aardvark.print_devices() # find Aardvark devices attached to this system
    1 device(s) found:
        port = 0   (avail)  (2237-889465)
    >>> with aardvark.Aardvark(0) as adapter:
    ...     adapter.target_power = True # enable power to the activity board
    ...     activity_board = tp240310.TP240310(i2c_master=adapter)
    ...     led = activity_board.d0
    ...     led.on()
