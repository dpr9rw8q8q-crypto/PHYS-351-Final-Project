import time
import csv
import RPi.GPIO as GPIO

# GPIO configuration (BCM numbering): edit these to match your wiring.
HCSR04_TRIG_PIN = 17
HCSR04_ECHO_PIN = 27

# Constants
SOUND_SPEED = 343.0  # m/s at 20 degrees C
TIMEOUT = 0.040
MAX_PULSE = 0.025
INTERVAL = 0.5  # Keep above 0.060 seconds between readings.


class HCSR04:
    def __init__(self, trig=HCSR04_TRIG_PIN, echo=HCSR04_ECHO_PIN):
        self.trig = trig
        self.echo = echo
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(trig, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(echo, GPIO.IN)
        time.sleep(0.1)

    def read_distance(self):
        """Return distance in meters, or None for an invalid reading."""
        if GPIO.input(self.echo) == GPIO.HIGH:
            return None

        # Send the trigger pulse.
        GPIO.output(self.trig, GPIO.HIGH)
        time.sleep(0.0001)
        GPIO.output(self.trig, GPIO.LOW)

        # Wait for Echo to rise.
        deadline = time.perf_counter() + TIMEOUT
        while GPIO.input(self.echo) == GPIO.LOW:
            if time.perf_counter() > deadline:
                return None
        start = time.perf_counter()

        # Wait for Echo to fall.
        while GPIO.input(self.echo) == GPIO.HIGH:
            if time.perf_counter() - start > TIMEOUT:
                return None
        duration = time.perf_counter() - start

        # Reject invalid echoes.
        if duration <= 0 or duration > MAX_PULSE:
            return None

        # Divide by two for the outward and return journey.
        return SOUND_SPEED * duration / 2
    

    def record(self, filename=None):
        """Print and save readings until Ctrl+C."""
        filename = filename or time.strftime("distance_%Y%m%d_%H%M%S.csv")
        with open(filename, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["time_s", "m", "cm", "mm", "inches", "status"])
            start = time.perf_counter()
            try:
                while True:
                    elapsed = round(time.perf_counter() - start, 3)
                    meters = self.read_distance()
                    if meters is None:
                        print("No valid echo")
                        writer.writerow([elapsed, "", "", "", "", "No valid echo"])
                    else:
                        cm = meters * 100
                        mm = meters * 1000
                        inches = cm / 2.54
                        print(f"{meters:.2f} m | {cm:.0f} cm | {mm:.0f} mm | {inches:.1f} in")
                        writer.writerow([elapsed, meters, cm, mm, inches, "OK"])
                    file.flush()
                    time.sleep(INTERVAL)
            except KeyboardInterrupt:
                print("\nStopped. Readings saved.")

    def close(self):
        GPIO.output(self.trig, GPIO.LOW)
        GPIO.cleanup((self.trig, self.echo))


# Test

def main():
    sensor = HCSR04()
    try:
        sensor.record()
    except KeyboardInterrupt:
        print("\nProgram ended.")
    finally:
        sensor.close()


if __name__ == "__main__":
    main()
