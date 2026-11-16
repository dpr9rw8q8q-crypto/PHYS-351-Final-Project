"""AW9523B GPIO helper and terminal test. Run python3 AW9523B.py --help."""

import argparse

ADDRESS = 0x58
ADDRESSES = range(0x58, 0x5C)

WIRING = """AW9523B -> Raspberry Pi (40-pin header)
  VIN/VCC -> 3.3 V (pin 1)
  GND     -> GND (pin 6)
  SDA     -> GPIO2 / SDA (pin 3)
  SCL     -> GPIO3 / SCL (pin 5)

Share SDA and SCL with other I2C devices, each at a unique address.
Do not use GPIO2 or GPIO3 for unrelated signals while using I2C.
Default address: 0x58 (Adafruit A0/A1 jumpers allow 0x59-0x5B).
INT and RST are optional on the Adafruit breakout.
Expander pins 0-15 are separate from the Pi's GPIO numbers.
For a button, use an external 10 kΩ pull-up to 3.3 V and switch to GND.
Digital I/O only in this helper: use Pi pins for precise pulses and PWM.
Use a driver for motors, servos, or solenoids; don't power them from the board.
"""


def scan_i2c():
    import board

    i2c = board.I2C()
    if not i2c.try_lock():
        raise RuntimeError("I2C bus is busy; stop other tests and retry.")
    try:
        return i2c.scan()
    finally:
        i2c.unlock()


class AW9523B:
    def __init__(self):
        self.expander = None

    def setup_pins(self, address=ADDRESS):
        """Initialize the board once. The driver resets all pins to inputs."""
        import adafruit_aw9523
        import board

        self.expander = adafruit_aw9523.AW9523(board.I2C(), address=address)

    def get_pin(self, number):
        """Return a GPIO-style pin with switch_to_input/output and .value."""
        if not 0 <= number <= 15:
            raise ValueError("Use an expander pin from 0 to 15.")
        if self.expander is None:
            raise RuntimeError("Call setup_pins() first.")
        return self.expander.get_pin(number)






def main():
    parser = argparse.ArgumentParser(
        description="Print AW9523B wiring, scan I2C, or read/write a digital pin.",
        epilog="Each read/write test initializes the board and resets its pin modes.",
    )
    parser.add_argument("--address", type=lambda value: int(value, 0),
                        choices=ADDRESSES, default=ADDRESS, metavar="0x58-0x5B")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("wiring", help="show the wiring without hardware")
    commands.add_parser("scan", help="list responding I2C addresses")
    for name in ("read", "write"):
        command = commands.add_parser(name, help=f"{name} an expander pin")
        command.add_argument("pin", type=int, choices=range(16), metavar="0-15")
        if name == "write":
            command.add_argument("value", type=int, choices=(0, 1))

    args = parser.parse_args()
    if args.command in (None, "wiring"):
        print(WIRING)
        return

    try:
        if args.command == "scan":
            addresses = scan_i2c()
            print("I2C addresses:", " ".join(f"0x{addr:02X}" for addr in addresses) or "none")
            for addr in addresses:
                if addr in ADDRESSES:
                    print(f"0x{addr:02X} is in the AW9523B address range.")
            return

        board_io = AW9523B()
        board_io.setup_pins(args.address)
        pin = board_io.get_pin(args.pin)
        if args.command == "read":
            pin.switch_to_input()
            value = int(pin.value)
        else:
            value = args.value
            pin.switch_to_output(value=bool(value))
        print(f"Expander pin {args.pin}: {value} ({'HIGH' if value else 'LOW'})")

    except ImportError as error:
        parser.exit(1, f"{error}\nInstall on the Pi: python3 -m pip install "
                    "adafruit-blinka adafruit-circuitpython-aw9523\n")
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"I2C error: {error}\nCheck I2C is enabled, then check wiring and address.\n")


if __name__ == "__main__":
    main()
