
from HCSR04 import HCSR04
from RGB import RGBLight
from DC_motor import DCMotor
from servo_motor import ServoMotor
from stepper_motor import StepperMotor



def main():
    # Detect a customer: take one distance reading in meters.
    sensor = HCSR04()
    try:
        distance = sensor.read_distance()
        print("Customer distance (m):", distance)
    finally:
        sensor.close()

    # Show that an order has been received
    light = RGBLight()
    try:
        light.on(color=1, duration=2)
    finally:
        light.close()

    # Move the cup table
    stepper1 = StepperMotor()
    try:
        stepper1.move(steps=50, step_delay=0.01, direction="cw")
    finally:
        stepper1.close()

    # Run the shaker motor briefly.
    motor = DCMotor()
    try:
        motor.run(freq=10, dc=50, duration=2)
    finally:
        motor.close()

    # Move the arm to a sample position.
    servo = ServoMotor()
    try:
        servo.move(angle=45, duration=2)
    finally:
        servo.close()

    print("Dummy component sequence finished.")
    # TODO: Add the real menu, order loop, and remaining sensors later.



if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram stopped.")
