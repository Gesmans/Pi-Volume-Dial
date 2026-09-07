from smbus2 import SMBus
from time import sleep

bus = SMBus(1)
ADDR = 0x4B

while True:
    bus.write_byte(ADDR, 0x84)
    value = bus.read_byte(ADDR)
    print(value)
    sleep(0.2)