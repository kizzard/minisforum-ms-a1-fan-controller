# MS-A1 Fan Controller
# ------------------------
# This script reads the temperature from a thermistor and adjusts the speed of a fan accordingly.
# It is designed to be run on a microcontroller compatible with CircuitPython, such as an
# Adafruit Feather or Raspberry Pi Pico.

# Set your desired temperature range and duty cycle range here
# Note that we are measuring the temperature of the heat sink, not the CPU.
# The heat sink will always be cooler than the CPU.
MAX_TEMP = 40           # Above this temp, run the fan at MAX_DUTY_CYCLE
MIN_TEMP = 30           # Below this temp, run the fan at MIN_DUTY_CYCLE
BAD_TEMP = 10           # If temp is below this, something is probably wrong with our thermistor
MIN_DUTY_CYCLE = 0.25   # 25% fan speed
MAX_DUTY_CYCLE = 1      # 100% fan speed
RAMP_UP_SECONDS = 5     # How long to take to ramp up to full speed
CYCLE_TIME_SECONDS = 1  # How often to check the temperature

# Thermistor parameters
THERMISTOR_NOMINAL = 10000  # Resistance at 25 degrees C
BETA_COEFFICIENT = 3950     # The beta coefficient of the thermistor
SERIES_RESISTOR = 10000     # The value of the 'other' resistor

import board
import adafruit_thermistor
import time
import pwmio

class rollingAverageFilter():
    def __init__(self, numSamples, initValue=0):
        self.samples = [initValue] * numSamples
        self.numSamples = numSamples
        self.value = sum(self.samples) / self.numSamples

    def update(self, value):
        self.samples = self.samples[1:]
        self.samples.append(value)
        self.value = sum(self.samples) / self.numSamples

RAMP_UP_CYCLES = int(RAMP_UP_SECONDS / CYCLE_TIME_SECONDS)

class Thermistor():
    def __init__(self, pin):
        self.thermistor = adafruit_thermistor.Thermistor(pin, THERMISTOR_NOMINAL, SERIES_RESISTOR, 25.0, BETA_COEFFICIENT, high_side=True)
        self.filter = rollingAverageFilter(RAMP_UP_CYCLES, self.thermistor.temperature)
        self.temperature = self.filter.value

    def update(self):
        self.filter.update(self.thermistor.temperature)
        self.temperature = self.filter.value if self.filter.value > 0 else 0


tempSensor = Thermistor(board.A0)
fan = pwmio.PWMOut(board.D0)

# Kick the fan on at 50% to start.
fan.duty_cycle = 2**15
time.sleep(2)

while True:
    tempSensor.update()
    t = tempSensor.temperature
    dutyCyclePercent = min(max((t - MIN_TEMP) / (MAX_TEMP - MIN_TEMP) * (MAX_DUTY_CYCLE - MIN_DUTY_CYCLE) + MIN_DUTY_CYCLE, MIN_DUTY_CYCLE), MAX_DUTY_CYCLE)
    if t <= BAD_TEMP:
        dutyCyclePercent = 1
    dutyCycleValue = min(int(dutyCyclePercent * 2**16), 65535)
    print('{}c, {}%'.format(int(t), int(dutyCyclePercent*100)))
    fan.duty_cycle = dutyCycleValue
    time.sleep(CYCLE_TIME_SECONDS)
