# Pico 2 measures the temperature of the heater and transmits it on the CAN bus.

from canio import Message, Match, RemoteTransmissionRequest
from MCP2515 import MCP2515 as CAN
from time import sleep_ms, ticks_ms
import asyncio, sys
import pwm, pid
import math

sleep_ms(2000)

# Ku = 0.5
# Tu = 101s

# Classic PID:
Kp = .3    # 0.6 * Ku
Ti = 50     # 0.5 * Tu
Td = 13     # 0.125 * Tu
integrationWorkingBand = (0.2, 2)

# matches = [
#     Match(0x8, mask=0x8, extended=True),
#     Match(0x10, mask=0x10, extended=True)
# ]

class CANHandler():
    def __init__(self):
        self._running = False
        self.temperature = [ ticks_ms() - 1500, None ]
        self.setpoint = [ ticks_ms() - 1500, None ]
        self.Kp = Kp
        self.Ti = Ti
        self.Td = Td
        self.can = CAN(0, 17, baudrate=125000)

    def start(self):
        self._running = True
        asyncio.create_task(self._receive())

    def stop(self):
        print("Stopping CANHandler")
        self._running = False

    async def _receive(self):
        listener = self.can.listen(timeout=1.0)
        while self._running:
            try:
                in_waiting = listener.in_waiting()
        
                for _i in range(in_waiting):
                    msg = listener.receive()
                    if isinstance(msg, Message):
                        if msg.id == 0x8:
                            if msg.data.decode() == "None":
                                self.temperature = [ ticks_ms(), None ]
                                continue
                            self.temperature = [ ticks_ms(), float(msg.data) ]
                            continue
                        if msg.id == 0xA:
                            self.setpoint = [ ticks_ms(), float("0."+msg.data.decode()) * 50 ]
                            continue
                        if msg.id == 0x11:
                            self.Kp = float(msg.data)
                            continue
                        if msg.id == 0x12:
                            self.Ti = float(msg.data)
                            continue
                        if msg.id == 0x13:
                            self.Td = float(msg.data)
                            continue

                    if isinstance(msg, RemoteTransmissionRequest):
                        if msg.id == 0x21:
                            self.can.send(Message(id=0x21, data=b"1", extended=True))
                            continue
                    
            except Exception as e:
                sys.print_exception(e)
        
            await asyncio.sleep(.1)



can = CANHandler()
pid = pid.PID(Kp, Ti, Td, can, integrationWorkingBand=integrationWorkingBand)
pwm = pwm.PWMController(1, pid, 1)

def atexit():
    pid.stop()
    pwm.stop()
    can.can.send(Message(id=0x9, data=b'0', extended=True))   # PWM duty
    can.can.send(Message(id=0x40, data=b'0', extended=True))  # PID P
    can.can.send(Message(id=0x41, data=b'0', extended=True))  # PID I
    can.can.send(Message(id=0x42, data=b'0', extended=True))  # PID D

async def main():
    can.start()
    pid.start()
    pwm.start()

    while can._running:
        print("")
        print("")
        print("Temperature: ", can.temperature[1])
        print("   Setpoint: ", can.setpoint[1])
        print("          P: ", pid._P)
        print("          I: ", pid._I)
        print("          D: ", pid._D)
        print("        PWM: ", pwm.duty)

        can.can.send(Message(id=0x9, data=str(pwm.duty)[0:8].encode(), extended=True)) # PWM duty
        can.can.send(Message(id=0x40, data=str(pid._P)[0:8].encode(), extended=True))  # PID P
        can.can.send(Message(id=0x41, data=str(pid._I)[0:8].encode(), extended=True))  # PID I
        can.can.send(Message(id=0x42, data=str(pid._D)[0:8].encode(), extended=True))  # PID D

        await asyncio.sleep(.1)

asyncio.run(main())