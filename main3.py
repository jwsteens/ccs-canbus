# Pico 2 measures the temperature of the heater and transmits it on the CAN bus.

import pico_functions_v1_1 as pf
from canio import Message, Match, RemoteTransmissionRequest
from MCP2515 import MCP2515 as CAN
from time import sleep_ms, ticks_ms
import asyncio, sys
from machine import Pin, ADC, UART

sleep_ms(1000)

led = Pin(25, Pin.OUT)

matches = [
    Match(0x8, mask=0x8, extended=True),
    Match(0x40, mask=0x40, extended=True)
]

class CANHandler():
    def __init__(self):
        self._running = False
        self.temperature = False
        self.PWM = False
        self.P = 0
        self.I = 0
        self.D = 0
        self.can = CAN(0, 17, baudrate=125000)
        self.available_nodes = { 1: ticks_ms() - 1500, 2: ticks_ms() - 1500}

    def start(self):
        self._running = True
        led.on()
        asyncio.create_task(self._receive())
        asyncio.create_task(self._heartbeat())

    def stop(self):
        self._running = False
        led.off()

    def _node_update(self, node: int):
        self.available_nodes[node] = ticks_ms()

    async def _heartbeat(self):
        while self._running:
            message = RemoteTransmissionRequest(id=0x21, length=1, extended=True)
            self.can.send(message)
            message = RemoteTransmissionRequest(id=0x22, length=1, extended=True)
            self.can.send(message)
            await asyncio.sleep(1)
    
    async def _receive(self):
        listener = self.can.listen(timeout=1.0, matches=matches)
        while self._running:
            try:
                in_waiting = listener.in_waiting()
        
                for _i in range(in_waiting):
                    msg = listener.receive()
                    if not isinstance(msg, Message): continue
                    if msg.id == 0x8:
                        if msg.data.decode() == "None":
                            self.temperature = None
                            self._node_update(2)
                            continue
                        self.temperature = float(msg.data)
                        self._node_update(2)
                        continue
                    if msg.id == 0x9:
                        self.PWM = float(msg.data.decode())
                        self._node_update(1)
                        continue
                    if msg.id == 0x40:
                        self.P = float(msg.data)
                        continue
                    if msg.id == 0x41:
                        self.I = float(msg.data)
                        continue
                    if msg.id == 0x42:
                        self.D = float(msg.data)
                        continue
                    if msg.id == 0x21:
                        self._node_update(1)
                        continue
                    if msg.id == 0x22:
                        self._node_update(2)
                        continue

                    
            except Exception as e:
                sys.print_exception(e)
        
            await asyncio.sleep(.1)
    


can = CANHandler()
pot = ADC(28)
oled = pf.display_init(ID=1, sda_pin=10, scl_pin=11)

ser = UART(0, baudrate=19200, tx=Pin(0), rx=Pin(1), timeout=2000)

async def main():
    can.start()

    while True:
        val = pf.adc_average(pot, 100)
        normedPot = pf.norm(val, 288, 65345)        
        if can.available_nodes[2] < (ticks_ms() - 1500):
            normedPot = 0
            can.temperature = None
        setpoint = round(normedPot * 50, 1)
        data = str(normedPot)[2:10].encode()
        if can.available_nodes[1] < (ticks_ms() - 1500):
            can.PWM = None
        
        can.can.send(Message(id=0xA, data=data, extended=True))
        # can.can.send(RemoteTransmissionRequest(id=0x21, length=1, extended=True))
        # can.can.send(RemoteTransmissionRequest(id=0x22, length=1, extended=True))

        ser.write(f'SP:{setpoint};PV:{can.temperature};PWM:{can.PWM};P:{can.P};I:{can.I};D:{can.D}\n')

        oled.fill(0)
        
        oled.text("    SP: " + str(setpoint), 12, 0, 1)
        oled.text("     T: " + str(round(can.temperature, 1) if can.temperature is not None else None), 12, 8, 1)
        oled.text("   PWM: " + str(round(can.PWM, 2) if can.PWM is not None else None), 12, 16, 1)
        oled.text("Node 1: " + str(can.available_nodes[1] > (ticks_ms() - 1500)), 12, 28, 1)
        oled.text("Node 2: " + str(can.available_nodes[2] > (ticks_ms() - 1500)), 12, 36, 1)
        pf.vert_level_indicator(normedPot, 0, 0, 64, 8, "bar", oled)
        if can.PWM is not None: pf.vert_level_indicator(can.PWM, 120, 0, 64, 8, "bar", oled)
        oled.show()

        print("")
        print("")
        print("   Setpoint: ", setpoint)
        print("Temperature: ", can.temperature)
        print("        PWM: ", can.PWM) 
        print("          P: ", can.P)
        print("          I: ", can.I)
        print("          D: ", can.D)
        print("      Nodes: ", can.available_nodes)

        await asyncio.sleep(.1)

asyncio.run(main())