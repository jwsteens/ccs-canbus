import asyncio, sys
from math import isnan
from machine import Pin, PWM

led = Pin(25, Pin.OUT)

def clamp(value, min_value, max_value):
    return max(min(value, max_value), min_value)

class PWMController():
    """"Control PWM signal based on PID output, gain and an optional bias. """
    def __init__(self, pin, pid, gain, bias=0, frequency=1000):
        self.pid = pid
        self.bias = bias
        self.gain = gain
        self._duty = 0
        self.output = PWM(Pin(pin), frequency)

        self._running = False

    def start(self):
        led.on()
        self._running = True
        asyncio.create_task(self._set_duty())

    def stop(self):
        self._running = False
        print("Stopping PWMController")
        self.pid.sensor.stop()

    @property
    def running(self):
        return self._running
    
    @property
    def duty(self):
        return self.output.duty_u16() / 65535
    
    async def _set_duty(self):
        while self._running: # 10Hz
            await asyncio.sleep(.1)
            try:                
                if self.pid.output is None:
                    self.stop()
                    continue
                self._duty = clamp(self.pid.output * self.gain + self.bias, 0, 1)
                # print(self.pid.output * self.gain + self.bias)
                duty_u16 = int(self._duty * 65535)
                self.output.duty_u16(duty_u16)
                continue

            except Exception as e:
                sys.print_exception(e)
                self.output.duty_u16(0)
                continue
        
        
        led.off()
        self.output.duty_u16(0)
        self._duty = 0
        return