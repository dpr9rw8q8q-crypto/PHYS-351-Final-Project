from pins import ExpanderPin, Pin, expander, pi_gpio
from time import sleep

# BCM GPIO for PWM; expander(0..15) for full on/off only.
DC_PWM_PIN = 12


class DCMotor:
    def __init__(self):
        # Pins are configured separately before using the component.
        pass

    def setup_pins(self, pin=DC_PWM_PIN, freq=10):
        self.pin = pin
        self.digital = Pin(pin, output=True) if isinstance(pin, ExpanderPin) else None
        if self.digital is not None:
            return
        GPIO = pi_gpio()
        GPIO.setup(pin, GPIO.OUT)
        self.pwm = GPIO.PWM(pin, freq)
        self.pwm.start(0)

    def start(self, freq=10, dc=50):
        """Run continuously; dc is a percentage from 0 to 100.
        
        Args:
            freq (float): Frequency in Hz.
            dc (float): Duty cycle percentage (0–100).
        """
        if self.digital is not None:
            if dc not in (0, 100):
                raise ValueError("DC motor speed control uses PWM; choose a Pi pin or 0/100%.")
            self.digital.write(dc == 100)
            return
        self.pwm.ChangeFrequency(freq)
        self.pwm.ChangeDutyCycle(dc)

    def run(self, freq, dc, duration):
        """Run for duration seconds, then stop.
        
        Args:
            freq (float): Frequency in Hz.
            dc (float): Duty cycle percentage (0–100).
            duration (float): Duration in seconds.
        """
        try:
            self.start(freq, dc)
            sleep(duration)
        finally:
            self.stop()

    def stop(self):
        """Stop the motor and set duty cycle to 0."""
        if self.digital is not None:
            self.digital.write(False)
        else:
            self.pwm.ChangeDutyCycle(0)

    def close(self):
        self.stop()
        if self.digital is not None:
            self.digital.close()
        else:
            self.pwm.stop()
            pi_gpio().cleanup(self.pin)








# Test

def main():
    motor = DCMotor()
    motor.setup_pins()
    try:
        motor.run(freq=10, dc=100 if motor.digital else 50, duration=5)
    except KeyboardInterrupt:
        print("\nProgram ended.")
    finally:
        motor.close()


if __name__ == "__main__":
    main()
