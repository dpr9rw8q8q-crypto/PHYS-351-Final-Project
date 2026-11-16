from pins import Pin, expander
from time import sleep

# Use BCM numbers or expander(0..15). Prefer Pi pins for faster stepping.
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

    def __init__(self):
        # Pins are configured separately before using the component.
        pass

    def setup_pins(self, pins=STEPPER_PINS, sleep_pin=STEPPER_SLEEP_PIN):
        self.sleep_pin = Pin(sleep_pin, output=True)
        self.pins = tuple(Pin(pin, output=True) for pin in pins)
        self._phase = None

    def move(self, steps=600, step_delay=0.01, direction="cw"):
        """Move full steps, then release the coils and put the driver to sleep."""
        # Sets direction: either +1 or -1 for clockwise or counterclockwise rotation.
        step_direction = 1 if direction == "cw" else -1
        try:
            self.sleep_pin.write(True)
            for _ in range(steps):
                # Preserve phase across calls so successive moves remain continuous.
                if self._phase is None:
                    self._phase = 0 if direction == "cw" else 3
                else:
                    self._phase = (self._phase + step_direction) % 4
                state = self.FULL_STEP_TABLE[self._phase]
                for pin, value in zip(self.pins, state):
                    pin.write(value)
                sleep(step_delay)
        finally:
            self.stop()

    def stop(self):
        self.sleep_pin.write(False)
        for pin in self.pins:
            pin.write(False)

    def close(self):
        self.stop()
        for pin in (*self.pins, self.sleep_pin):
            pin.close()








# Test

def main():
    motor = StepperMotor()
    motor.setup_pins()
    try:
        motor.move(steps=600, step_delay=0.01, direction="ccw")
    except KeyboardInterrupt:
        print("\nProgram ended.")
    finally:
        motor.close()


if __name__ == "__main__":
    main()
