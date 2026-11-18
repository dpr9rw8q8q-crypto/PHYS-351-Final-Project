#!/usr/bin/env python3
"""Read-only Raspberry Pi header/GPIO report. Optional I2C probes: --scan BUS."""
import argparse
from pathlib import Path
import re
import shutil
import subprocess

# Written using ChatGPT, a useful tool to list all GPIO pins and I2C devices on a Raspberry Pi.
# It is read-only and does not change any pin states. It can be run on a local computer to check for I2C devices, but the GPIO report will only work on a Pi.

# Physical positions on the standard Raspberry Pi 40-pin header.
HEADER = [
    '3.3V', '5V', 2, '5V', 3, 'GND', 4, 14, 'GND', 15,
    17, 18, 27, 'GND', 22, 23, '3.3V', 24, 10, 'GND',
    9, 25, 11, 8, 'GND', 7, 0, 1, 5, 'GND',
    6, 12, 13, 'GND', 19, 16, 26, 20, 'GND', 21,
]


def read(path):
    try:
        return Path(path).read_text().strip()
    except (OSError, UnicodeError):
        return ''


def run(args):
    if not shutil.which(args[0]):
        return '', f'{args[0]} not installed'
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=20)
        return p.stdout, (p.stderr.strip() or f'exit {p.returncode}') if p.returncode else ''
    except (OSError, subprocess.TimeoutExpired) as exc:
        return '', str(exc)


def parse_gpioinfo(output):
    chips = {}
    chip = None
    for row in output.splitlines():
        match = re.match(r'(gpiochip\d+)\s+-\s+\d+ lines:', row)
        if match:
            chip = match[1]
            chips[chip] = {}
        match = re.match(r'\s*line\s+(\d+):\s+(.*)', row)
        if match and chip:
            detail = match[2]
            consumer = re.search(r'consumer="([^"]+)"', detail)
            # libgpiod v1 prints consumer as a second quoted column.
            quoted = re.findall(r'"([^"]*)"', detail)
            owner = consumer[1] if consumer else (quoted[1] if len(quoted) > 1 else '')
            chips[chip][int(match[1])] = (owner, detail)
    return chips


def pin_states(output):
    states = {}
    for row in output.splitlines():
        m = re.match(r'\s*(\d+):\s+(.*?)\s*//\s*(.*)', row)
        if m:
            function = m[3].split('=', 1)[-1].strip()
            level = re.search(r'\|\s*(hi|lo|--)', m[2])
            states[int(m[1])] = (function, level[1] if level else '?')
    return states


def chip_paths():
    result = {}
    for root in ('/sys/bus/gpio/devices', '/sys/class/gpio'):
        for path in Path(root).glob('gpiochip*'):
            # Match the character-device name, not legacy sysfs base numbers.
            dev = read(path / 'dev')
            if dev and Path('/sys/dev/char', dev).exists():
                resolved = Path('/sys/dev/char', dev).resolve()
                result[resolved.name] = resolved
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scan', type=int, action='append', default=[], metavar='BUS',
                        help='probe this I2C bus (repeatable); probes can disturb some devices')
    args = parser.parse_args()
    if any(bus < 0 for bus in args.scan):
        parser.error('bus numbers must be nonnegative')
    pin_text, pin_err = run(['pinctrl', 'get'])
    gpio_text, gpio_err = run(['gpioinfo'])
    states = pin_states(pin_text)
    chips = parse_gpioinfo(gpio_text)
    paths = chip_paths()
    header_chip = next((name for name, path in paths.items()
                        if any(x in read(path / 'label').lower()
                               for x in ('pinctrl-rp1', 'pinctrl-bcm'))), None)
    if not header_chip:
        header_chip = next((name for name, lines in chips.items()
                            if any('"ID_SDA"' in detail or '"GPIO27"' in detail
                                   or '"GP27"' in detail for _, detail in lines.values())), None)
    owners = chips.get(header_chip, {})
    print('\nRASPBERRY PI PIN REPORT')
    print('Connected wires cannot be detected reliably. Unclaimed does not mean disconnected.')
    print('\n40-PIN HEADER (physical numbering)')
    print(f'{"Pin":>3}  {"Signal":<9} {"Configuration / software owner":<43} Level')
    for physical, signal in enumerate(HEADER, 1):
        if isinstance(signal, str):
            status, level, label = 'Power/ground; connection unknown', '-', signal
        else:
            label = f'GPIO{signal}'
            function, level = states.get(signal, ('unknown', '?'))
            owner = owners.get(signal, ('', ''))[0]
            if owner:
                status = f'CLAIMED: {owner} ({function})'
            elif function not in ('none', 'input', 'unknown'):
                status = f'CONFIGURED: {function}; connection unknown'
            else:
                status = f'{function}; no reported claim; connection unknown'
            if signal in (0, 1):
                status += '; ID reserved'
        print(f'{physical:>3}  {label:<9} {status:<43} {level}')
    print('\nI2C BUSES / MUX CHANNELS (registered with Linux)')
    root = Path('/sys/bus/i2c/devices')
    buses = sorted(root.glob('i2c-*'), key=lambda p: int(p.name.split('-')[1]))
    for bus in buses:
        number = int(bus.name.split('-')[1])
        print(f'  Bus {number}: {read(bus / "name") or "name unknown"}')
        mux = bus / 'mux_device'
        if mux.exists():
            parent = mux.resolve()
            channel = next((p.name for p in parent.glob('channel-*')
                            if p.resolve() == bus.resolve()), 'channel unknown')
            print(f'    Mux {parent.name}, {channel}')
        devices = sorted(root.glob(f'{number}-*'))
        for device in devices:
            driver = device / 'driver'
            print(f'    0x{device.name.split("-")[1]}: {read(device / "name") or "device"}'
                  f' (registered; driver {driver.resolve().name if driver.exists() else "unbound"})')
        if not devices:
            print('    No registered devices; physical connections unknown.')
    if not buses:
        print('  No buses found. Check that I2C is enabled.')
    print('\nI2C GPIO EXPANDERS')
    found = False
    for chip, path in sorted(paths.items()):
        address = next((p.name for p in (path, *path.parents)
                        if re.fullmatch(r'\d+-[0-9a-f]{4}', p.name)), None)
        if not address:
            continue
        found = True
        bus, addr = address.split('-')
        print(f'  {chip}: {read(path / "label")} | bus {bus}, address 0x{addr}')
        lines = chips.get(chip, {})
        count = int(read(path / 'ngpio') or len(lines))
        for offset in range(count):
            owner, detail = lines.get(offset, ('', ''))
            direction = re.search(r'\b(input|output)\b', detail)
            status = f'CLAIMED: {owner}' if owner else 'No reported claim; connection unknown'
            print(f'    {offset:>2}: {direction[1] if direction else "?":<6} {status}')
    if not found:
        print('  None exposed as GPIO controllers by Linux.')
    print('  Undriven boards and boards managed by Python libraries may not appear here.')
    print('  An address response alone cannot identify an expander or its pin wiring.')
    for bus in dict.fromkeys(args.scan):
        print(f'\nI2C BUS {bus} PROBE (addresses, not pin connections)')
        output, error = run(['i2cdetect', '-y', str(bus)])
        if error:
            print(f'  Scan failed: {error}')
            continue
        responses = []
        for row in output.splitlines():
            m = re.match(r'^([0-9a-f]{2}):\s+(.*)', row)
            if m:
                for offset, token in enumerate(m[2].split()):
                    # First row omits reserved addresses 0x00..0x02.
                    address = int(m[1], 16) + offset + (3 if m[1] == '00' else 0)
                    if token == 'UU':
                        responses.append(f'0x{address:02x}: driver claimed')
                    elif re.fullmatch(r'[0-9a-f]{2}', token):
                        responses.append(f'0x{token}: responded')
        print('  ' + ('; '.join(responses) or 'No responses; this does not prove no devices are connected.'))
    for error in (pin_err, gpio_err):
        if error:
            print(f'\nNote: {error}')
    print('\nTip: sudo python3 gpio_report.py gives permission to inspect GPIO metadata.')
    print('Optional: --scan 1 probes header I2C bus 1; use only with probe-safe devices.\n')




if __name__ == '__main__':
    main()
