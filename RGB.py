from gpiozero import RGBLED
from time import sleep

# GPIO configuration (BCM numbering): edit these to match your wiring.
RGB_RED_PIN = 22
RGB_GREEN_PIN = 17
RGB_BLUE_PIN = 27
RGB_ACTIVE_HIGH = True  # False for a common-anode LED.


class RGBLight:
    # Columns are [red, green, blue]: 
    # Rows: red, green, blue, yellow, cyan, magenta, white.
    COLORS = [
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
        [1, 1, 0],
        [0, 1, 1],
        [1, 0, 1],
        [1, 1, 1],
    ]

    def __init__(self, red=RGB_RED_PIN, green=RGB_GREEN_PIN, blue=RGB_BLUE_PIN,
                 active_high=RGB_ACTIVE_HIGH):
        self.led = RGBLED(red=red, green=green, blue=blue, active_high=active_high)

    def set_color(self, color):
        """Set a color index (0–6) and leave the LED on."""
        self.led.color = self.COLORS[color]

    def on(self, color, duration):
        """Show a color for duration seconds, then turn off."""
        try:
            self.set_color(color)
            sleep(duration)
        finally:
            self.off()

    def off(self):
        """ Turns off the LED """
        self.led.off()

    def close(self):
        """ Propeerly closes the LED and releases GPIO resources """
        self.led.close()








# Test

def main():
    light = RGBLight()
    try:
        light.on(color=1, duration=5)
    except KeyboardInterrupt:
        print("\nProgram ended.")
    finally:
        light.close()


if __name__ == "__main__":
    main()
