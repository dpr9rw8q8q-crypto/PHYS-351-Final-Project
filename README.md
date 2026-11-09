# PHYS-351-Final-Project
PHYS 351 Final Project


# Hardware Component Reference

Quick guide to the hardware modules, pin mappings, and methods used in this project.

---

## 1. HCSR04 (Ultrasonic Distance Sensor)

Measures customer/object distance using ultrasonic sound waves and can record readings to CSV.

**Default Pins:** `trig = 17`, `echo = 27` (BCM)

### Methods

#### `__init__(trig=17, echo=27)`
Initializes trigger as an output (low) and echo as an input.

#### `read_distance()`
Sends a 10 µs pulse and listens for the echo pulse. Returns the measured distance in meters, or `None` if the echo times out or is invalid.

#### `record(filename=None)`
Continuously logs readings (m, cm, mm, in) to the console and a CSV file until interrupted with `Ctrl+C`.

#### `close()`
Sets the trigger pin low and cleans up the trigger and echo GPIO pins.

---

## 2. DCMotor (DC Shaker Motor)

Controls speed and run duration of a DC motor using software PWM.

**Default Pin:** `pin = 12` (BCM)

### Methods

#### `__init__(pin=12, freq=10)`
Configures the motor pin as a PWM output at the specified frequency and starts at 0% duty cycle.

#### `start(freq=10, dc=50)`
Runs the motor continuously at the given frequency (Hz) and duty cycle (0–100%).

#### `run(freq, dc, duration)`
Runs the motor at the chosen speed and duty cycle for `duration` seconds, then automatically stops it.

#### `stop()`
Sets duty cycle back to 0% to stop rotation.

#### `close()`
Stops PWM output and cleans up the motor's GPIO pin.

---

## 3. RGBLight (Status LED)

Controls a common-cathode/anode RGB LED using `gpiozero` presets to signal project states.

**Default Pins:** `red = 22`, `green = 17`, `blue = 27` (BCM)

### Color Table Index (0–6)

| Index | Color |
|-------|-------|
| `0` | Red |
| `1` | Green |
| `2` | Blue |
| `3` | Yellow |
| `4` | Cyan |
| `5` | Magenta |
| `6` | White |

### Methods

#### `__init__(red=22, green=17, blue=27, active_high=True)`
Sets up the red, green, and blue pins using `gpiozero.RGBLED`.

#### `set_color(color)`
Sets the LED color using index `0` to `6` and leaves it lit.

#### `on(color, duration)`
Turns the LED to the chosen color for `duration` seconds, then turns it off.

#### `off()`
Turns off all three color channels.

#### `close()`
Shuts off the LED and releases the GPIO pins.

---

## 4. StepperMotor (Turntable Motor)

Controls a bipolar stepper motor (NEMA 17) step-by-step using a full-step phase table and a sleep line.

**Default Pins:**

- `pins = (4, 22, 17, 27)` — `AIN1`, `AIN2`, `BIN1`, `BIN2`
- `sleep_pin = 26` (BCM)

### Methods

#### `__init__(pins=(4, 22, 17, 27), sleep_pin=26)`
Configures all coil pins and the driver sleep pin as outputs set to low.

#### `move(steps=600, step_delay=0.01, direction="cw")`
Wakes the motor driver (`sleep_pin` high), rotates the motor for `steps` count in `"cw"` or `"ccw"`, maintains continuous phase tracking between moves, and puts the driver back to sleep when done.

#### `stop()`
Sets all coil pins low and sets `sleep_pin` low to power down the driver.

#### `close()`
Calls `stop()` and cleans up all stepper GPIO pins.

---

## 5. ServoMotor (Positioning Arm Servo)

Controls an arm servo motor by mapping degrees to PWM duty cycles using a linear calibration formula.

**Default Pin:** `pin = 17` (BCM)

**Fitting Formula:** *[Insert calibration formula here]*

### Methods

#### `__init__(pin=17)`
Configures the pin for 50 Hz PWM (20 ms period) and initializes at 0% duty cycle.

#### `set_angle(angle)`
Calculates the duty cycle from the linear calibration formula and applies it immediately.

#### `servo_motor(angle, duration)`
Recalibrates through home position (`7.5%` duty), moves to `angle`, holds for `duration` seconds, and turns off PWM signal upon completion.

#### `move(angle, duration)`
Convenience helper that executes `servo_motor(angle, duration)`.

#### `stop()`
Sets PWM duty cycle to 0 to disable holding torque and reduce jitter.

#### `close()`
Stops the PWM instance and cleans up the servo GPIO pin.
