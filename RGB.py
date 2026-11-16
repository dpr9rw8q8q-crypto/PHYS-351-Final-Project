"""Adafruit #3350 RGB button control. Assisted by ChatGPT."""

from time import sleep

from pins import Pin, expander

# BCM GPIO numbers or expander(0..15). RGB pins drive MOSFET gates.
RGB_RED_PIN = 6
RGB_GREEN_PIN = 16
RGB_BLUE_PIN = 20
BUTTON_PIN = 5
RGB_ACTIVE_HIGH = True  # HIGH at the gate pulls the ring cathode LOW.


class RGBLight:
    COLORS = {
        "red": (1, 0, 0),
        "green": (0, 1, 0),
        "blue": (0, 0, 1),
        "yellow": (1, 1, 0),
        "cyan": (0, 1, 1),
        "magenta": (1, 0, 1),
        "white": (1, 1, 1),
    }

    def setup_pins(self, red=RGB_RED_PIN, green=RGB_GREEN_PIN, blue=RGB_BLUE_PIN,
                   active_high=RGB_ACTIVE_HIGH, *, button=BUTTON_PIN):
        self.active_high = active_high
        self.channels = [Pin(pin, output=True, initial=not active_high)
                         for pin in (red, green, blue)]
        # Use an external 10 kΩ pull-up to 3.3 V on the switch input.
        self.button = Pin(button) if button is not None else None

    def is_pressed(self):
        """Read the momentary switch. Pressing connects the input to GND."""
        if self.button is None:
            raise RuntimeError("No switch input configured.")
        return not self.button.read()

    def set_color(self, color):
        """Set a named color or a legacy index (0–6)."""
        if type(color) is int and 0 <= color < len(self.COLORS):
            color = tuple(self.COLORS)[color]
        if not isinstance(color, str) or color.lower() not in self.COLORS:
            raise ValueError("Choose red, green, blue, yellow, cyan, magenta, or white.")
        for pin, enabled in zip(self.channels, self.COLORS[color.lower()]):
            pin.write(bool(enabled) == self.active_high)

    def on(self, color="blue", duration=None):
        """Light the ring until off(), or for duration seconds if given."""
        self.set_color(color)
        if duration is not None:
            try:
                sleep(duration)
            finally:
                self.off()

    def off(self):
        for pin in self.channels:
            pin.write(not self.active_high)

    def close(self):
        self.off()
        for pin in self.channels:
            pin.close()
        if self.button is not None:
            self.button.close()






# Test

def main():
    light = RGBLight()
    light.setup_pins()
    try:
        print("Blue = idle; green = pressed. Ctrl+C to stop.")
        last = None
        while True:
            pressed = light.is_pressed()
            if pressed != last:
                light.on(color="green" if pressed else "blue")
                last = pressed
            sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        light.close()


if __name__ == "__main__":
    main()
