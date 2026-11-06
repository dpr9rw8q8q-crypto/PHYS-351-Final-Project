import RPi.GPIO as GPIO
from time import sleep

# GPIO configuration (BCM numbering): edit these to match your wiring.
DC_PWM_PIN = 12


class DCMotor:
    def __init__(self, pin=DC_PWM_PIN, freq=10):
        self.pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        self.pwm = GPIO.PWM(pin, freq)
        self.pwm.start(0)

    def start(self, freq=10, dc=50):
        """Run continuously; dc is a percentage from 0 to 100.
        
        Args:
            freq (float): Frequency in Hz.
            dc (float): Duty cycle percentage (0–100).
        """
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
        self.pwm.ChangeDutyCycle(0)

    def close(self):
        self.pwm.stop()
        GPIO.cleanup(self.pin)








# Test

def main():
    motor = DCMotor()
    try:
        motor.run(freq=10, dc=50, duration=5)
    except KeyboardInterrupt:
        print("\nProgram ended.")
    finally:
        motor.close()


if __name__ == "__main__":
    main()
