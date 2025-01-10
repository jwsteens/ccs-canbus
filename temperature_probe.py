from machine import Pin
import onewire, ds18x20, asyncio
from time import sleep_ms

led = Pin(25, Pin.OUT)

class Sensor():
    """Retrieve temperature from DS18B20 sensor. Pin must be provided."""
    def __init__(self, pin):
        self.pin = Pin(pin)
        self.value = False
        self.temperature = None

        self._ds = ds18x20.DS18X20(onewire.OneWire(Pin(15)))
        self._running = False

        roms = self._ds.scan()
        if not roms: return None

        self._rom = roms[0]



    def start(self):
        self._running = True
        led.on()
        asyncio.create_task(self._get_temperature())



    def stop(self):
        self._running = False
        led.off()



    async def _get_temperature(self):
        while True: # 10Hz
            try:
                if not self._running:
                    self.temperature = None
                    return

                self._ds.convert_temp()
                await asyncio.sleep(.1)
                self.temperature = self._ds.read_temp(self._rom)
                continue

            except Exception as e:
                await asyncio.sleep(.1)
                roms = self._ds.scan()
                self.temperature = None
                if len(roms) > 0:
                    self._rom = roms[0]
                    continue
