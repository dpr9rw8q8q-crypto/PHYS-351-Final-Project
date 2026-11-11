
from HCSR04 import HCSR04
from RGB import RGBLight
from DC_motor import DCMotor
from servo_motor import SolenoidValve
from stepper_motor import StepperMotor



# GPIO pins for each component (BCM numbering).
# These preserve the current wiring; some pins overlap, so tests run one at a time.
SENSOR_TRIG_PIN = 17
SENSOR_ECHO_PIN = 2
LIGHT_RED_PIN = 22
LIGHT_GREEN_PIN = 17
LIGHT_BLUE_PIN = 27

DC_MOTOR_PIN = 12

STEPPER_AIN1_PIN = 4
STEPPER_AIN2_PIN = 22
STEPPER_BIN1_PIN = 17
STEPPER_BIN2_PIN = 27
STEPPER_SLEEP_PIN = 26


def main():
    # Detect a customer: take one distance reading in meters.
    sensor = HCSR04()
    sensor.setup_pins(trig=SENSOR_TRIG_PIN, echo=SENSOR_ECHO_PIN)
    try:
        distance = sensor.read_distance()
        print("Customer distance (m):", distance)
    finally:
        sensor.close()

    # Show that an order has been received
    light = RGBLight()
    light.setup_pins(red=LIGHT_RED_PIN, green=LIGHT_GREEN_PIN, blue=LIGHT_BLUE_PIN)
    try:
        light.on(color=1, duration=2)
    finally:
        light.close()

    # Move the cup table
    stepper1 = StepperMotor()
    stepper1.setup_pins(
        pins=(STEPPER_AIN1_PIN, STEPPER_AIN2_PIN, STEPPER_BIN1_PIN, STEPPER_BIN2_PIN),
        sleep_pin=STEPPER_SLEEP_PIN,
    )
    try:
        stepper1.move(steps=50, step_delay=0.01, direction="cw")
    finally:
        stepper1.close()

    # Run the shaker motor briefly.
    motor = DCMotor()
    motor.setup_pins(pin=DC_MOTOR_PIN)
    try:
        motor.run(freq=10, dc=50, duration=2)
    finally:
        motor.close()

    # Briefly energize the valve at full duty.
    valve = SolenoidValve()
    valve.setup_pins()
    try:
        valve.run(duty_cycle=100, duration=0.5)
    finally:
        valve.close()

    print("Dummy component sequence finished.")
    # TODO: Add the real menu, order loop, and remaining sensors later.
    # Duplicate component example (choose a different, unused GPIO pin):
    # motor2 = DCMotor()
    # motor2.setup_pins(pin=DC_MOTOR_2_PIN)
    # Define DC_MOTOR_2_PIN in the GPIO section above, then use and close motor2.




if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram stopped.")
