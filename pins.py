"""Digital pins: use a BCM integer or expander(0..15) in component settings.

Made with assistance from ChatGPT 6.1 Sol
"""

from dataclasses import dataclass
from functools import lru_cache

from assets.AW9523B import ADDRESS, ADDRESSES, AW9523B


@dataclass(frozen=True)
class ExpanderPin:
    number: int
    address: int


def expander(number, *, address=ADDRESS):
    if type(number) is not int or not 0 <= number <= 15:
        raise ValueError("Use an expander pin from 0 to 15.")
    if address not in ADDRESSES:
        raise ValueError("Use an AW9523B address from 0x58 to 0x5B.")
    return ExpanderPin(number, address)


@lru_cache(maxsize=None)
def _board(address):
    board = AW9523B()
    board.setup_pins(address)
    return board


def pi_gpio():
    import RPi.GPIO as GPIO

    GPIO.setmode(GPIO.BCM)
    return GPIO


def require_pi(pin, signal):
    if type(pin) is not int:
        raise ValueError(f"{signal} needs a native Pi BCM pin for timing.")
    return pin


class Pin:
    """GPIO-style digital input or output on either board."""

    def __init__(self, assignment, *, output=False, initial=False):
        self.assignment = assignment
        self.output = output
        if isinstance(assignment, ExpanderPin):
            self.io = _board(assignment.address).get_pin(assignment.number)
            if output:
                self.io.switch_to_output(value=bool(initial))
            else:
                self.io.switch_to_input()
        else:
            self.gpio = gpio = pi_gpio()
            if output:
                gpio.setup(assignment, gpio.OUT, initial=int(bool(initial)))
            else:
                gpio.setup(assignment, gpio.IN)

    def read(self):
        if isinstance(self.assignment, ExpanderPin):
            return bool(self.io.value)
        return bool(self.gpio.input(self.assignment))

    def write(self, value):
        if not self.output:
            raise ValueError("Configure the pin as an output before writing.")
        if isinstance(self.assignment, ExpanderPin):
            self.io.value = bool(value)
        else:
            self.gpio.output(self.assignment, int(bool(value)))

    def close(self):
        if isinstance(self.assignment, ExpanderPin):
            self.io.switch_to_input()
        else:
            self.gpio.cleanup(self.assignment)

