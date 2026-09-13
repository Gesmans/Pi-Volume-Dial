# Pi Volume Dial

A physical volume knob for a Raspberry Pi 5. Turning a potentiometer sets the system volume on a Bluetooth speaker, shows the level on a 10-segment LED bar graph, and prints the percentage to a 1602 LCD.

Built as a physical computing exercise — the interesting part isn't the volume control, it's that the Pi can't read an analogue input at all without help.

## The problem

A Raspberry Pi's GPIO pins are digital. They read HIGH or LOW and nothing in between. A potentiometer outputs a smoothly varying voltage — 0V at one stop, 3.3V at the other. Wire the wiper straight to a GPIO and you get a single flip from 0 to 1 somewhere around the middle of the knob's travel. Everything useful is thrown away.

The fix is an ADC (analogue-to-digital converter). This project uses an **ADS7830** — 8 channels, 8-bit resolution, talks over I2C.

## Hardware

| Component | Notes |
|---|---|
| Raspberry Pi 5 | Bookworm, PipeWire audio stack |
| ADS7830 ADC breakout | I2C, address `0x4B` |
| 10kΩ rotary potentiometer | 3 pins, wiper to ADC channel A0 |
| 10-segment LED bar graph | Common cathode, one 220Ω resistor per segment |
| 1602 LCD with PCF8574 backpack | I2C, address `0x27`, 5V |
| Bluetooth speaker | Any paired output device |

### Wiring

**Potentiometer**
```
outer pin  → 3.3V
outer pin  → GND
wiper      → ADS7830 A0
```

Use 3.3V, not 5V. A 5V wiper voltage will damage the Pi's GPIO.

**I2C bus** — both devices share the same two lines:
```
SDA → BCM 2  (physical pin 3)
SCL → BCM 3  (physical pin 5)
```

The ADC runs on 3.3V; the LCD backpack wants 5V.

**Bar graph** — anodes to GPIO through a 220Ω resistor each, cathodes to a shared ground rail. BCM pins used, bottom segment first:

```
4, 27, 17, 6, 13, 19, 26, 16, 20, 21
```

### Verifying the bus

```bash
i2cdetect -y 1
```

Both `27` and `4b` should appear. If only one shows, the wiring is wrong.

## Software setup

```bash
sudo apt install python3-smbus2
pip install gpiozero RPLCD
```

On Bookworm, `pip install` into the system Python is blocked by an externally-managed-environment error. Either use the apt package as above, or a venv created with `--system-site-packages` so gpiozero stays visible.

## Reading the ADC

The ADS7830 isn't supported by gpiozero, so it's driven directly over I2C. Write a command byte selecting the channel, then read one byte back:

```python
from smbus2 import SMBus

bus = SMBus(1)
ADDR = 0x4B

bus.write_byte(ADDR, 0x84)   # channel 0, single-ended
value = bus.read_byte(ADDR)  # 0-255
```

`0x84` is the command byte for channel 0 in single-ended mode. Other channels use different bytes — see the datasheet.

Measured range across the full sweep of the pot: **0 to 254**.

## Scaling

One reading, two destinations, two different divisors:

```python
lit    = int(value / 25.5)  # 0-10, LED segments
volume = value / 255        # 0.0-1.0, wpctl
```

255 ÷ 10 = 25.5 counts per segment. The volume figure must stay a float — wrapping it in `int()` collapses it to 0 or 1.

## Driving the LEDs

```python
for i in range(10):
    if i < lit:
        leds[i].on()
    else:
        leds[i].off()
```

`i < lit` rather than `i == lit` — a bar, not a single segment. It also means index 10 is never reached, so `lit` hitting 10 is safe.

## Setting the volume

Bookworm uses PipeWire. `amixer` shows nothing useful and `pactl` isn't installed by default. The working tool is `wpctl`:

```bash
wpctl status                  # find the sink ID
wpctl set-volume 78 0.5
```

From Python:

```python
import subprocess
subprocess.run(["wpctl", "set-volume", SINK_ID, str(volume)])
```

**Known limitation:** the sink ID is assigned at connection time and changes when the speaker reconnects or the Pi reboots. Hardcoding it works for a bench setup but breaks on reboot. Resolving the device by name is the fix.

## LCD output

Clearing the whole display every loop causes visible strobing. Reset the cursor and overwrite in place instead:

```python
lcd.cursor_pos = (0, 0)
lcd.write_string(f"Volume: {int(volume * 100)}% ")
```

The trailing space matters — without it, `100%` dropping to `50%` leaves a stray `0` on screen.

## Gotchas worth knowing

- **Pi 5 has no analogue input.** No ADC, no pot. There's no software workaround.
- **Pi 5 has no 3.5mm jack.** Audio is HDMI, USB, or Bluetooth only.
- **HDMI audio exposes no mixer control.** `amixer scontrols` returns empty, so there's no system volume to set over HDMI.
- **Two I2C devices on one bus is fine.** Each has its own address; the Pi puts the address on the wire first and only the matching device replies.
- **Unconditional loops are wasteful.** Reading every 100ms fires 10 subprocess calls per second whether the knob moved or not. Comparing against the previous reading avoids that — though ADC jitter of a count or two can defeat it.

## Planned

- **74HC595 shift register** for the bar graph. Drops the display from 10 GPIO pins to 3. Two chips chained give 16 outputs from those same 3 pins, since the overflow pin (QH′) feeds the next chip's serial input.
- **Resolve the audio sink by name** rather than by ID, so it survives a reboot.
- **Debounce the ADC reading** to stop jitter triggering redundant updates.

## Licence

MIT
