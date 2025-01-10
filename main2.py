# Pico 2 measures the temperature of the heater and transmits it on the CAN bus.

from canio import Message
from MCP2515 import MCP2515 as CAN
from time import sleep_ms
import asyncio
import temperature_probe

sleep_ms(1000)

sensor = temperature_probe.Sensor(15)
can = CAN(0, 17, baudrate = 125000)

async def main():
    sensor.start()

    while True:
        print("")
        print("")
        print("Temperature: ", sensor.temperature)

        message = Message(id=0x8, data=str(sensor.temperature).encode(), extended=True)
        can.send(message)

        await asyncio.sleep(.1)

asyncio.run(main())