from website import website_start
from HCSR04 import HCSR04
from LIS3DH import LIS3DH
from RGB import RGBLight
from DC_motor import DCMotor
from servo_motor import SolenoidValve
from stepper_motor import StepperMotor
import time
from pins import expander

# Maybe use JScratch canvas to create an animated menu.
# Add multi-threading to run the web server so it is always on.

# Use BCM GPIO numbers or expander(0..15) where the component supports it.
# Keep HC-SR04 trigger/echo on the Pi; expander motor/valve outputs are on/off only.
# These preserve the current wiring; some pins overlap, so tests run one at a time.
SENSOR_TRIG_PIN = 17
SENSOR_ECHO_PIN = 27

LIGHT_RED_PIN = 6
LIGHT_GREEN_PIN = 16
LIGHT_BLUE_PIN = 20
LIGHT_BUTTON_PIN = 5

DC_MOTOR_PIN = 12

STEPPER_AIN1_PIN = 4
STEPPER_AIN2_PIN = 22
STEPPER_BIN1_PIN = 17
STEPPER_BIN2_PIN = 27
STEPPER_SLEEP_PIN = 26

print("test")

def main():

    # 1. Detect a customer: take one distance reading in meters.
    sensor = HCSR04()
    sensor.setup_pins(trig=SENSOR_TRIG_PIN, echo=SENSOR_ECHO_PIN)
    try:
        distance = sensor.read_distance()
        # Wait until a customer is detected within the specified range, in meters.
        while distance > 0.5: 
            time.sleep(0.1)
            distance = sensor.read_distance()
            print("Customer distance (m):", distance)

        print("Customer detected within range!")
    finally:
        sensor.close()

    website_start()  # Start the web server for the user to select options.

    # After customer comes within range, a display will say something like "Welcome Guest".
    # Then the display will switch to a web interface for the user to begin picking their options.
    # After the options are chosen, it is the nsubmitted and the python records these options as variables.
    # Those stored variables are then used as the settings fro the tea making process.





if __name__ == "__main__":
    try:
        main()
        # Make it when program ended, it will cycle and begin main() again.
    except KeyboardInterrupt:
        print("\nProgram stopped.")
