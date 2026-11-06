import RPi.GPIO as GPIO
from time import sleep

# BCM GPIO pin connected to servo PWM wire
SERVO_PWM_PIN = 17


class ServoMotor:
    # Lower and upper measured duty cycle limits
    LOWER_DUTY = 3.2 # %
    UPPER_DUTY = 11.3 # %
    # Lower and upper measured angle limits
    LOWER_ANGLE = -83.0
    UPPER_ANGLE = 75.0

    # Fitting formula: (duty cycle) = Ma + B (where a is angle)
    #   M and B below were gathered from taking the lower and higher angle limits and their
    #.  coresponding duty cycle limits and solving for M and B in the linear equation.
    M = 0.05137
    B = 7.4555

    def __init__(self, pin=SERVO_PWM_PIN):
        self.pin = pin
        # BCM GPIO pin connected to servo PWM wire
        # Sets pin numbering ID to BCM mode
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)

        # Create a 50 Hz PWM signal through BCM PIN
        self.servo = GPIO.PWM(pin, 50) # 20 ms frame
        self.servo.start(0) # Beginning at 0 duty cycle


    def servo_motor(self, angle, duration):
        """ Moves the servo motor to a specified angle for a certain duration.
     
        Args:
            angle (float): The angle to move the servo to, in degrees.
            duration (float): The duration in seconds to hold the position.
         """

        try:
            # Move servo to zero position
            #   Duty cycle values above and below this may turn the motor
            #   clockwise and counterclockwise
            self.servo.ChangeDutyCycle(7.5)
            sleep(0.3)

            # Check if angle is within measured servo range
            # Confirm this manually before calling: -83 to 75 degrees.

            # Calculate duty cycle using fitting formula
            duty = (self.M * angle) + self.B
            # Check if calculated duty cycle is within measured limits
            # The measured limits above are retained for reference.

            # Prints the fit equation result
            print(f"\nFit Equation: duty = ({self.M} * {angle}) + {self.B} = {duty:.2f}")

            # Move servo to requested angle
            self.set_angle(angle)
            sleep(duration)

            # Prints resulting movement in degrees and the duty cycle.
            print(f"Servo moved to about {angle} degrees.")
            print(f"Duty cycle: {duty:.2f}%")

            # Stop sending movement

        finally:
            self.stop()


    def set_angle(self, angle):
        duty = self.M * angle + self.B
        self.servo.ChangeDutyCycle(duty)
        return duty

    def move(self, angle, duration):
        self.servo_motor(angle, duration)

    def stop(self):
        self.servo.ChangeDutyCycle(0)

    def close(self):
        self.servo.stop()
        GPIO.cleanup(self.pin)


def main():
    motor = ServoMotor()
    try:
        motor.move(angle=45, duration=5)
    except KeyboardInterrupt:
        print("\nProgram ended.")
    finally:
        motor.close()


if __name__ == "__main__":
    main()
