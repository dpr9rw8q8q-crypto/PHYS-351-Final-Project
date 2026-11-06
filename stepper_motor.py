import RPi.GPIO as GPIO
from time import sleep

# GPIO configuration (BCM numbering):
STEPPER_AIN1_PIN = 4
STEPPER_AIN2_PIN = 22
STEPPER_BIN1_PIN = 17
STEPPER_BIN2_PIN = 27
STEPPER_SLEEP_PIN = 26

# Defines the GPIO pins for the stepper motor coils and sleep pin as constants.
STEPPER_PINS = (
    STEPPER_AIN1_PIN, 
    STEPPER_AIN2_PIN, 
    STEPPER_BIN1_PIN, 
    STEPPER_BIN2_PIN
    )


class StepperMotor:
    # NEMA17: 200 full steps per revolution.
    FULL_STEP_TABLE = [
        # AIN1, AIN2, BIN1, BIN2
        # Pin0, Pin1, Pin2, Pin3
        [1, 0, 1, 0], # A+ B+
        [0, 1, 1, 0], # A- B+
        [0, 1, 0, 1], # A- B-
        [1, 0, 0, 1], # A+ B-
    ]

    def __init__(self, pins=STEPPER_PINS, sleep_pin=STEPPER_SLEEP_PIN):
        self.pins = tuple(pins)
        self.sleep_pin = sleep_pin
        self._phase = None
        GPIO.setmode(GPIO.BCM)
        for pin in (*self.pins, self.sleep_pin):
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

    def move(self, steps=600, step_delay=0.01, direction="cw"):
        """Move full steps, then release the coils and put the driver to sleep."""
        # Sets direction: either +1 or -1 for clockwise or counterclockwise rotation.
        step_direction = 1 if direction == "cw" else -1
        try:
            GPIO.output(self.sleep_pin, GPIO.HIGH)
            for _ in range(steps):
                # Preserve phase across calls so successive moves remain continuous.
                if self._phase is None:
                    self._phase = 0 if direction == "cw" else 3
                else:
                    self._phase = (self._phase + step_direction) % 4
                state = self.FULL_STEP_TABLE[self._phase]
                GPIO.output(self.pins, state)
                sleep(step_delay)
        finally:
            self.stop()

    def stop(self):
        GPIO.output(self.pins, GPIO.LOW)
        GPIO.output(self.sleep_pin, GPIO.LOW)

    def close(self):
        self.stop()
        GPIO.cleanup((*self.pins, self.sleep_pin))








# Test

def main():
    motor = StepperMotor()
    try:
        motor.move(steps=600, step_delay=0.01, direction="ccw")
    except KeyboardInterrupt:
        print("\nProgram ended.")
    finally:
        motor.close()


if __name__ == "__main__":
    main()
