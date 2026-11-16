#!/usr/bin/env python3
"""
LIS3DH Triple-Axis Accelerometer Module for Raspberry Pi.

Contributors:
- Matt Dyson (mattdyson.org)
- Adapted by Bill Cooke (Removed dependency on Adafruit I2C in favor of smbus2)
- Modified on 10/20/2024 by Ran Yang
- Revised on 9/26/2026: address check, datasheet scale factors, setClick fix

Note: 
- As of 1/1/2020, this script is strictly Python 3, tested on v3.10.2.
- The chip address can be found using: sudo i2cdetect -y 1
  - Identified bus: smbus2.SMBus(1)
  - Chip address: 0x18 (Hex 18 = Decimal 24) when SDO is left open or tied to GND
                  0x19 (Hex 19 = Decimal 25) when SDO is tied to 3.3V
  - The MCP9808 temperature sensor also uses 0x18. If both are on the bus, tie the
    LIS3DH SDO pin to 3.3V and use: acc = LIS3DH(address=0x19)
    i2cdetect should then show both 18 (MCP9808) and 19 (LIS3DH).

I2C Pin Configuration:
- Raspberry Pi 4 and 5: GPIO2 (SDA), GPIO3 (SCL)
- LIS3DH: 
  - Vdd -> GPIO1 (3.3V)
  - Gnd -> Any GPIO ground
  - SCL -> GPIO3
  - SDA -> GPIO2

SPI Pin Configuration (this module uses I2C only):
- Raspberry Pi 4 and 5: GPIO11 (SCLK), GPIO10 (MOSI), GPIO09 (MISO)
- LIS3DH: 
  - Vdd -> GPIO1 (3.3V)
  - Gnd -> Any GPIO ground
  - SCL -> GPIO11
  - SDA -> GPIO10
  - SDO -> GPIO09
  - CS -> Any GPIO (Active low for SPI data communication)
  
Additional Notes:
- 3Vo is an output pin, max 100mA. Leave floating.
- For multiple LIS3DH chips on a single master, they can share data and clock lines but should have distinct CS pins.
"""


import smbus2
import time
import RPi.GPIO as GPIO  # needed for Hardware interrupt


class LIS3DH:

    # Ranges
    RANGE_2G = 0b00
    RANGE_4G = 0b01
    RANGE_8G = 0b10
    RANGE_16G = 0b11

    # Refresh rates
    DATARATE_POWERDOWN = 0      # Power down
    DATARATE_1HZ = 0b0001
    DATARATE_10HZ = 0b0010
    DATARATE_25HZ = 0b0011
    DATARATE_50HZ = 0b0100
    DATARATE_100HZ = 0b0101
    DATARATE_200HZ = 0b0110
    DATARATE_400HZ = 0b0111
    DATARATE_LOWPOWER_1K6HZ = 0b1000  # Low power mode (1.6KHz)
    # Low power mode (5KHz) / Normal power mode (1.25KHz)
    DATARATE_LOWPOWER_5KHZ = 0b1001

    # Registers
    REG_STATUS1 = 0x07
    REG_OUTADC1_L = 0x08
    REG_OUTADC1_H = 0x09
    REG_OUTADC2_L = 0x0A
    REG_OUTADC2_H = 0x0B
    REG_OUTADC3_L = 0x0C
    REG_OUTADC3_H = 0x0D
    REG_INTCOUNT = 0x0E
    REG_WHOAMI = 0x0F  # Device identification register
    REG_TEMPCFG = 0x1F
    REG_CTRL1 = 0x20  # Used for data rate selection, and enabling/disabling individual axis
    REG_CTRL2 = 0x21
    REG_CTRL3 = 0x22
    REG_CTRL4 = 0x23  # Used for BDU, scale selection, resolution selection and self-testing
    REG_CTRL5 = 0x24
    REG_CTRL6 = 0x25
    REG_REFERENCE = 0x26
    REG_STATUS2 = 0x27
    REG_OUT_X_L = 0x28
    REG_OUT_X_H = 0x29
    REG_OUT_Y_L = 0x2A
    REG_OUT_Y_H = 0x2B
    REG_OUT_Z_L = 0x2C
    REG_OUT_Z_H = 0x2D
    REG_FIFOCTRL = 0x2E
    REG_FIFOSRC = 0x2F
    REG_INT1CFG = 0x30
    REG_INT1SRC = 0x31
    REG_INT1THS = 0x32
    REG_INT1DUR = 0x33
    REG_CLICKCFG = 0x38
    REG_CLICKSRC = 0x39
    REG_CLICKTHS = 0x3A
    REG_TIMELIMIT = 0x3B
    REG_TIMELATENCY = 0x3C
    REG_TIMEWINDOW = 0x3D

    # Values
    DEVICE_ID = 0x33
    INT_IO = 0x04           # GPIO pin for interrupt
    CLK_NONE = 0x00
    CLK_SINGLE = 0x01
    CLK_DOUBLE = 0x02

    # Axes
    AXIS_X = 0x00
    AXIS_Y = 0x01
    AXIS_Z = 0x02

    def __init__(self, address=0x18, debug=False):
        """Initialize the accelerometer with the given I2C address."""
        self.isDebug = debug
        self.debug("Initialising LIS3DH")
        self.bus = smbus2.SMBus(1)
        self.address = address

        if not self._device_connected():
            raise Exception(
                f"No LIS3DH found at address 0x{self.address:02X}. "
                "Run 'i2cdetect -y 1'. If the MCP9808 is also at 0x18, "
                "tie the LIS3DH SDO pin to 3.3V and use LIS3DH(address=0x19).")

        self.configure_defaults()

    def _device_connected(self):
        """Check that a LIS3DH answers at self.address: WHO_AM_I (0x0F) must read 0x33."""
        try:
            device_id = self.bus.read_byte_data(self.address, self.REG_WHOAMI)
        except OSError:  # nothing answered at this address
            return False
        return device_id == self.DEVICE_ID

    def configure_defaults(self):
        """Configure default settings for the accelerometer."""
        self.setAxisStatus(self.AXIS_X, True)
        self.setAxisStatus(self.AXIS_Y, True)
        self.setAxisStatus(self.AXIS_Z, True)
        self.setDataRate(self.DATARATE_400HZ)
        self.setHighResolution()
        self.setBDU()
        self.setRange(self.RANGE_2G)

    def getX(self):
        return self.getAxis(self.AXIS_X)

    def getY(self):
        return self.getAxis(self.AXIS_Y)

    def getZ(self):
        return self.getAxis(self.AXIS_Z)

    def getAxis(self, axis):
        # Determine registers to read (2 per axis)
        base_register = self.REG_OUT_X_L + (2 * axis)
        low_byte = self.bus.read_byte_data(self.address, base_register)
        high_byte = self.bus.read_byte_data(self.address, base_register + 1)

        combined_value = low_byte | (high_byte << 8)
        corrected_value = self.twosComp(combined_value)

        # Counts per g in high-resolution mode (datasheet Table 4):
        # 12-bit data are left-justified in 16 bits, so divide by 16,
        # then multiply by the sensitivity: 1, 2, 4 or 12 mg per digit.
        # For example, 2G: 16 / 0.001 g = 16000 counts per g.
        range_divisors = {
            self.RANGE_2G: 16000,
            self.RANGE_4G: 8000,
            self.RANGE_8G: 4000,
            self.RANGE_16G: 1333.33
        }

        # Get the current range and compute the result
        current_range = self.getRange()
        divisor = range_divisors.get(current_range)

        # Handle potential unknown ranges
        if divisor is None:
            raise ValueError(f"Unknown range: {current_range}")

        return float(corrected_value) / divisor

    # Get the range that the sensor is currently set to

    def getRange(self):
        val = self.bus.read_byte_data(self.address, self.REG_CTRL4)
        range_bits = (val >> 4) & 0b0011

        range_map = {
            self.RANGE_2G: self.RANGE_2G,
            self.RANGE_4G: self.RANGE_4G,
            self.RANGE_8G: self.RANGE_8G
        }

        return range_map.get(range_bits, self.RANGE_16G)

    # Set the range of the sensor (2G, 4G, 8G, 16G)

    def setRange(self, range_value):
        if range_value < 0 or range_value > 3:
            raise ValueError("Invalid range value specified.")

        ctrl_val = self.bus.read_byte_data(self.address, self.REG_CTRL4)

        # Clear the bits responsible for the range setting
        ctrl_val &= ~(0b110000)

        # Set the new range
        ctrl_val |= (range_value << 4)

        self.writeRegister(self.REG_CTRL4, ctrl_val)

    # Enable or disable an individual axis
    # Read status from CTRL_REG1, then write back with appropriate status bit changed

    def setAxisStatus(self, axis, enable):
        if axis < 0 or axis > 2:
            raise Exception("Tried to modify invalid axis")

        current = self.bus.read_byte_data(self.address, self.REG_CTRL1)
        status = 1 if enable else 0
        final = self.setBit(current, axis, status)
        self.writeRegister(self.REG_CTRL1, final)

    def setInterrupt(self, mycallback):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.INT_IO, GPIO.IN)
        GPIO.add_event_detect(self.INT_IO, GPIO.RISING, callback=mycallback)

    def setClick(self, clickmode, clickthresh=80, timelimit=10, timelatency=20, timewindow=100, mycallback=None):
        if (clickmode == self.CLK_NONE):
            val = self.bus.read_byte_data(
                self.address, self.REG_CTRL3)  # Get value from register
            val &= ~(0x80)  # unset bit 8 to disable interrupt
            self.writeRegister(self.REG_CTRL3, val)  # Write back to register
            self.writeRegister(self.REG_CLICKCFG, 0)  # disable all interrupts
            return
        self.writeRegister(self.REG_CTRL3, 0x80)  # turn on int1 click
        self.writeRegister(self.REG_CTRL5, 0x08)  # latch interrupt on int1

        if (clickmode == self.CLK_SINGLE):
            # turn on all axes & singletap
            self.writeRegister(self.REG_CLICKCFG, 0x15)
        if (clickmode == self.CLK_DOUBLE):
            # turn on all axes & doubletap
            self.writeRegister(self.REG_CLICKCFG, 0x2A)

    # set timing parameters
        self.writeRegister(self.REG_CLICKTHS, clickthresh)
        self.writeRegister(self.REG_TIMELIMIT, timelimit)
        self.writeRegister(self.REG_TIMELATENCY, timelatency)
        self.writeRegister(self.REG_TIMEWINDOW, timewindow)

        if mycallback != None:
            self.setInterrupt(mycallback)

    def getClick(self):
        reg = self.bus.read_byte_data(
            self.address, self.REG_CLICKSRC)       # read click register
        # reset  interrupt flag
        self.bus.read_byte_data(self.address, self.REG_INT1SRC)
        return reg

    # Set the rate (cycles per second) at which data is gathered

    def setDataRate(self, dataRate):
        val = self.bus.read_byte_data(
            self.address, self.REG_CTRL1)  # Get current value
        val &= 0b1111  # Mask off lowest 4 bits
        val |= (dataRate << 4)  # Write in our new data rate to highest 4 bits
        self.writeRegister(self.REG_CTRL1, val)  # Write back to register

    # Set whether we want to use high resolution or not

    def setHighResolution(self, highRes=True):
        val = self.bus.read_byte_data(
            self.address, self.REG_CTRL4)  # Get current value
        status = 1 if highRes else 0
        # High resolution (HR) is bit 3 of REG_CTRL4
        final = self.setBit(val, 3, status)
        self.writeRegister(self.REG_CTRL4, final)

    # Set whether we want to use block data update or not
    # False = output registers not updated until MSB and LSB reading

    def setBDU(self, bdu=True):
        val = self.bus.read_byte_data(
            self.address, self.REG_CTRL4)  # Get current value
        status = 1 if bdu else 0
        # Block data update (BDU) is bit 7 of REG_CTRL4
        final = self.setBit(val, 7, status)
        self.writeRegister(self.REG_CTRL4, final)

    # Write the given value to the given register

    def writeRegister(self, register, value):
        self.debug("WRT %s to register 0x%X" % (bin(value), register))
        self.bus.write_byte_data(self.address, register, value)

    # Print the value stored in a register, e.g. printRegister(REG_WHOAMI) prints 0x33 (51)

    def printRegister(self, register):
        value = self.bus.read_byte_data(self.address, register)
        print(f'LIS3DH register 0x{register:02X} reads 0x{value:02X} ({value})')

    # Set the bit at index 'bit' to 'value' on 'input' and return

    def setBit(self, input, bit, value):
        mask = 1 << bit
        input &= ~mask
        if value:
            input |= mask
        return input

    def twosComp(self, x):
        """Convert 16-bit two's complement value to a signed integer."""
        if x & 0x8000:
            return -((0x10000 - x) & 0xFFFF)
        return x

    # Print an output of all registers

    def dumpRegisters(self):
        for x in range(0x0, 0x3D):
            read = self.bus.read_byte_data(self.address, x)
            print("%X: %s" % (x, bin(read)))

    def debug(self, message):
        if not self.isDebug:
            return
        print(message)
