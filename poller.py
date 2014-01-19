
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# jan 2014 bbb garden shield attempt
# AKA

'''
Sensors:
analog level sensor, pin AIN0
TMP102 i2c temperature sensor, address 0x48
(if add0 is grounded) or 0x49 (if pulled up)


Outputs:
Analog RGB LED strip
I2C display(?)
Pump Activate/Deactivate (GPIO pin)

'''
from Adafruit_I2C import Adafruit_I2C
import time
import atexit
import Adafruit_BBIO.UART as uart
import Adafruit_BBIO.PWM as pwm
import Adafruit_BBIO.GPIO as gpio
import Adafruit_BBIO.ADC as adc
import TMP102 as tmp102
import datetime
import random
import tempodb
import key


interval = 20 # seconds between samples
greenPin = 'P8_13'
bluePin = 'P9_14'
redPin = 'P8_19'
servoPin = 'P9_16'
readings = []

def exit_handler():
    print 'exiting'
    pwm.stop(greenPin)
    pwm.stop(redPin)
    pwm.stop(bluePin)
    pwm.stop(servoPin)
    pwm.cleanup()

def do_sensor_read(self):
    self.print 'sensor read'
    readings = []
    # value = ADC.read("AIN1")
    # adc returns value from 0 to 1.
    # use read_raw(pin) to get V values
    tank = adc.read('AIN0')
    self.print tank
    photo = adc.read('AIN1')
    self.print photo
    readings.append({'key':'tankLevel','v': tank}) # tank level
    readings.append({'key':'photocell','v': photo}) # photocell
    # readings.append({'air_temp': t.getTemp()})

def do_db_update(self):
    self.print 'db update'
    client = tempodb.Client(key.API_KEY, key.API_SECRET)
    date = datetime.datetime.now()
    self.print date
    client.write_bulk(date, readings)


def do_state_display(self):
    print 'state_display'

print 'starting sampling at'
print datetime.datetime.now()
adc.setup()
# t = tmp102.TMP102()
# NOTE
# There is currently a bug in the ADC driver.
# You'll need to read the values twice
# in order to get the latest value.
pwm.start(greenPin, 10.0, 2000.0)
pwm.start(redPin, 10.0, 2000.0)
pwm.start(bluePin, 10.0, 2000.0)
atexit.register(exit_handler)

while True:
    try:
        do_sensor_read()
    except:
        pass
    try:
        do_db_update()
    except:
        pass
    try:
        do_state_display()
    except:
        pass
    # time.sleep(interval)