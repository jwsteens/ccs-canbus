import asyncio, sys
from time import ticks_ms
from collections import deque

DERIVATION_TIME = 5 # seconds
FREQUENCY = 10 # Hz
THERMAL_RUNAWAY_TIME = 120 # seconds

def clamp(value, min_value, max_value):
    return max(min(value, max_value), min_value)

class PID():
    """Calculate PID output based on input and setpoint. KP, TI, TD and sensor object must be provided."""
    def __init__(self, KP, TI, TD, sensor, setpoint=0, integrationWorkingBand=(0, 100)):
        self.KP = KP
        self.TI = TI
        self.TD = TD
        self.setpoint = setpoint
        self.sensor = sensor
        self.integrationWorkingBand = integrationWorkingBand

        self.output = False

        self._P = 0
        self._I = 0
        self._D = 0
        
        self._running = False
        self._integral = 0
        self._temperature_history = deque([(ticks_ms(), 0)], int(THERMAL_RUNAWAY_TIME * FREQUENCY))
        self._output_history = None # This value is used to indicate when the output value was above 90% for the first time

    def start(self):
        self._running = True
        asyncio.create_task(self._calculate())

    def stop(self):
        self._running = False

    def _calculate_I(self, error, dt):
        integral_step = error * dt
        if abs(self._D) > 1:
            self._integral = 0
            self._I = 0
            return

        if  abs(error) > self.integrationWorkingBand[1]:
            self._integral = 0
            self._I = 0
            return

        if abs(self._D) > .2: return

        if abs(error) < self.integrationWorkingBand[0]: return
        
        self._integral += error * dt
        self._I = clamp(self._integral / self.TI, 0, 1)
        return

    @property
    def running(self):
        return self._running

    async def _calculate(self):
        while self._running: # 10Hz
            await asyncio.sleep(1 / FREQUENCY)
            try:
                if not self._running:
                    self.output = None
                    return
                
                if not self.sensor.temperature[1]: # Failsafe: no temperature data
                    self.output = 0
                    continue
                
                now = ticks_ms() / 1000 # seconds
                last_error = list(self._temperature_history)[-1]
                dt = (now - last_error[0]) # exact time since last calculation
                oldest_temperature = list(self._temperature_history)[0]
                min_index = clamp(DERIVATION_TIME * FREQUENCY, 0, len(self._temperature_history) - 1)
                temp_5s = list(self._temperature_history)[-min_index]
                
                # Calculate proportional
                error = self.sensor.setpoint[1] - self.sensor.temperature[1]
                self._P = self.KP * error

                if len(self._temperature_history) == DERIVATION_TIME * FREQUENCY:
                    # Calculate integral
                    self._calculate_I(error, dt)

                    # Calculate derivative
                    self._D = self.TD * -(self.sensor.temperature[1] - temp_5s[1]) / (now - temp_5s[0])

                self.output = self._P + self._I + self._D

                # Integrity check
                if self.output > .9 and self._output_history is None:
                    self._output_history = ticks_ms()

                if self.output < .9:
                    self._output_history = None

                if (
                    self._output_history
                    and ticks_ms() - self._output_history > THERMAL_RUNAWAY_TIME * 1000
                    and self.sensor.temperature[1] - oldest_temperature[1] < 0.1
                ):
                    print("THERMAL RUNAWAY PROTECTION")
                    self.stop()

                # Temperature history
                if len(self._temperature_history) >= DERIVATION_TIME * FREQUENCY:
                    self._temperature_history.popleft()

                self._temperature_history.append((now, self.sensor.temperature[1]))
                continue

            except Exception as e:
                sys.print_exception(e)
                self.output = 0
                continue

        self.output = None
