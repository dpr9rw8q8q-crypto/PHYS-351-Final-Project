import time
from assets.LIS3DHMOD import LIS3DH as LIS3DHDriver

# Accelerometer address on I2C.
ADDRESS = 0x18
INTERVAL = 0.5

# Check I2C bus: i2cdetect -y 1

class LIS3DH:
    def __init__(self):
        self.sensor = None

    def setup_pins(self, address=ADDRESS):
        # I2C uses the Pi's SDA and SCL pins.
        self.sensor = LIS3DHDriver(address=address)
        self.sensor.setDataRate(self.sensor.DATARATE_100HZ)
        time.sleep(0.1)

    def read_acceleration(self):
        """Return X, Y, and Z acceleration in g."""
        return self.sensor.getX(), self.sensor.getY(), self.sensor.getZ()

    def close(self):
        if self.sensor is not None:
            self.sensor.bus.close()
            self.sensor = None





# Test

def main():
    sensor = LIS3DH()
    try:
        sensor.setup_pins()
        while True:
            x, y, z = sensor.read_acceleration()
            print(f"X: {x:+.3f} g | Y: {y:+.3f} g | Z: {z:+.3f} g")
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        sensor.close()


if __name__ == "__main__":
    main()
