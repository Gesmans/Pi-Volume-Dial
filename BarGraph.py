from smbus2 import SMBus
from gpiozero import LED
from time import sleep


bus = SMBus(1) # Initialize the I2C bus
ADDR = 0x4b # Address of the Arduino
lit = 0 # Initialize the lit variable

PINS = [4, 27, 17, 6, 13, 19, 26, 16, 20, 21] # GPIO pins for the LEDs
leds = [LED(p) for p in PINS] # Initialize LEDs

while True:
    bus.write_byte(ADDR, 0x84) # Request data from the Arduino
    value = bus.read_byte(ADDR) # Read the data
    lit = int(value / 25.5) # Calculate the number of LEDs to light up based on the value (0-255)
    print(value, lit) # Print the value and the number of LEDs to light up
    for i in range(10): # Loop through the LEDs
        if i < lit: # If the index is less than the number of LEDs to light up
            leds[i].on() # Turn on the LED
        else: # If the index is greater than or equal to the number of LEDs to light up
            leds[i].off() # Turn off the LED