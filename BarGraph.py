import subprocess
from smbus2 import SMBus
from gpiozero import LED
from time import sleep

bus = SMBus(1) # Initialize the I2C bus
RASP = 0x4b # Address of the Raspberry Pi
lit = 0 # Initialize the lit variable
volume = 0 # Initialize the volume variable

PINS = [4, 27, 17, 6, 13, 19, 26, 16, 20, 21] # GPIO pins for the LEDs 
leds = [LED(p) for p in PINS] # Initialize LEDs

while True:
    bus.write_byte(RASP, 0x84) # Request data from the Raspberry Pi
    value = bus.read_byte(RASP) # Read the data
    lit = int(value / 25.5) # Calculate the number of LEDs to light up based on the value (0-255)
    print(value, lit, volume) # Print the value and the number of LEDs to light up
    subprocess.run(["wpctl", "set-volume", "86", str(volume)]) # Set the volume using wpctl command
    volume = value / 255
    for i in range(10): # Loop through the LEDs
        if i < lit: # If the index is less than the number of LEDs to light up
            leds[i].on() # Turn on the LED
        else: # If the index is greater than or equal to the number of LEDs to light up
            leds[i].off() # Turn off the LED
    sleep(0.1) # Sleep for 0.1 seconds before the next iteration

