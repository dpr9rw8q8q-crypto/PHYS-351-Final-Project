import time
import csv
from pins import Pin, require_pi

# Code Works

# Native BCM pins only: trigger and echo use short pulses.
HCSR04_TRIG_PIN = 17
HCSR04_ECHO_PIN = 27

# Constants
SOUND_SPEED = 343.0  # m/s at 20 degrees C
TIMEOUT = 0.040
MAX_PULSE = 0.025
INTERVAL = 0.5  # Keep above 0.060 seconds between readings.


class HCSR04:
    def __init__(self):
        # Pins are configured separately before using the component.
        pass

    def setup_pins(self, trig=HCSR04_TRIG_PIN, echo=HCSR04_ECHO_PIN):
        require_pi(trig, "HC-SR04 trigger")
        require_pi(echo, "HC-SR04 echo")
        self.trig = Pin(trig, output=True)
        self.echo = Pin(echo)
        time.sleep(0.1)

    def read_distance(self):
        """Return distance in meters, or None for an invalid reading.
        
        Returns distance in meters.
        """
        if self.echo.read():
            return None

        # Send the trigger pulse.
        self.trig.write(True)
        time.sleep(0.0001)
        self.trig.write(False)

        # Wait for Echo to rise.
        deadline = time.perf_counter() + TIMEOUT
        while not self.echo.read():
            if time.perf_counter() > deadline:
                return None
        start = time.perf_counter()

        # Wait for Echo to fall.
        while self.echo.read():
            if time.perf_counter() - start > TIMEOUT:
                return None
        duration = time.perf_counter() - start

        # Reject invalid echoes.
        if duration <= 0 or duration > MAX_PULSE:
            return None

        # Divide by two for the outward and return journey.
        meters = SOUND_SPEED * duration / 2
        cm = meters * 100
        mm = meters * 1000
        inches = cm / 2.54
        print(f"{meters:.2f} m | {cm:.0f} cm | {mm:.0f} mm | {inches:.1f} in")
        return meters

    def close(self):
        self.trig.write(False)
        self.trig.close()
        self.echo.close()






# Test

def main():
    sensor = HCSR04()
    sensor.setup_pins()
    try:
        sensor.read_distance()
    except KeyboardInterrupt:
        print("\nProgram ended.")
    finally:
        sensor.close()


if __name__ == "__main__":
    main()
