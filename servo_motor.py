"""PWM control for an active-high DC solenoid valve driver."""

from math import isfinite
from time import sleep

from pins import ExpanderPin, Pin, expander, pi_gpio


# BCM GPIO for PWM; expander(0..15) for full on/off only.
SOLENOID_PWM_PIN = 23


class SolenoidValve:
    def setup_pins(self, pin=SOLENOID_PWM_PIN, *, frequency=50):
        if not isfinite(frequency) or frequency <= 0:
            raise ValueError("Frequency must be positive.")
        self.pin = pin
        self.digital = Pin(pin, output=True) if isinstance(pin, ExpanderPin) else None
        if self.digital is not None:
            return
        GPIO = pi_gpio()
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
        self.pwm = GPIO.PWM(pin, frequency)
        self.pwm.start(0)

    def run(self, duty_cycle, duration):
        """Energize at 0–100% duty for duration seconds, then switch off."""
        if not 0 <= duty_cycle <= 100:
            raise ValueError("Duty cycle must be between 0 and 100.")
        if not isfinite(duration) or duration < 0:
            raise ValueError("Duration must be finite and nonnegative.")
        if self.digital is not None and duty_cycle not in (0, 100):
            raise ValueError("Partial solenoid duty uses PWM; choose a Pi pin or 0/100%.")
        try:
            if self.digital is not None:
                self.digital.write(duty_cycle == 100)
            else:
                self.pwm.ChangeDutyCycle(duty_cycle)
            sleep(duration)
        finally:
            self.stop()

    def stop(self):
        if self.digital is not None:
            self.digital.write(False)
        else:
            self.pwm.ChangeDutyCycle(0)

    def close(self):
        try:
            self.stop()
            if self.digital is None:
                self.pwm.stop()
        finally:
            if self.digital is not None:
                self.digital.close()
            else:
                pi_gpio().cleanup(self.pin)





# Test

def main():
    valve = SolenoidValve()
    valve.setup_pins()
    try:
        print("Opening the solenoid valve for 1 second.")
        valve.run(duty_cycle=100, duration=1)
    except KeyboardInterrupt:
        print("\nProgram ended.")
    finally:
        valve.close()


if __name__ == "__main__":
    main()
