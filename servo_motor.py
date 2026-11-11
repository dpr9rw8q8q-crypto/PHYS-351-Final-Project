"""PWM control for an active-high DC solenoid valve driver."""

from math import isfinite
from time import sleep

import RPi.GPIO as GPIO


SOLENOID_PWM_PIN = 23


class SolenoidValve:
    def setup_pins(self, pin=SOLENOID_PWM_PIN, *, frequency=50):
        if not isfinite(frequency) or frequency <= 0:
            raise ValueError("Frequency must be positive.")
        self.pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
        self.pwm = GPIO.PWM(pin, frequency)
        self.pwm.start(0)

    def run(self, duty_cycle, duration):
        """Energize at 0–100% duty for duration seconds, then switch off."""
        if not 0 <= duty_cycle <= 100:
            raise ValueError("Duty cycle must be between 0 and 100.")
        if not isfinite(duration) or duration < 0:
            raise ValueError("Duration must be finite and nonnegative.")
        try:
            self.pwm.ChangeDutyCycle(duty_cycle)
            sleep(duration)
        finally:
            self.stop()

    def stop(self):
        self.pwm.ChangeDutyCycle(0)

    def close(self):
        try:
            self.stop()
            self.pwm.stop()
        finally:
            GPIO.cleanup(self.pin)
