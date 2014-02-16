
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
from __future__ import division
import time
import atexit
import Adafruit_BBIO.UART as uart
import Adafruit_BBIO.PWM as pwm
import Adafruit_BBIO.GPIO as gpio
import Adafruit_BBIO.ADC as adc
import TMP102 as tmp102
import datetime
from dateutil.tz import tzlocal
import random
import tempodb
import key
from math import log

BCOEFFICIENT = 3950 # thermistor beta coefficient
THERMISTORNOMINAL = 10000
TEMPERATURENOMINAL = 25.0
SERIESRESISTOR = 10000

interval = 120 # seconds between samples
greenPin = 'P8_13'
bluePin = 'P9_14'
redPin = 'P8_19'
servoPin = 'P9_16'
tankPin = 'AIN0'
photoPin = 'AIN3'
thermistor1 = 'AIN1' # bed temp
thermistor2 = 'AIN2' # reservoir temp
pumpPin = 'P8_10'
readings = []

def exit_handler():
    print 'exiting'
    pwm.stop(greenPin)
    pwm.stop(redPin)
    pwm.stop(bluePin)
    pwm.stop(servoPin)
    pwm.cleanup()
    gpio.output(pumpPin,gpio.LOW)
    gpio.cleanup()

def do_sensor_read():
    print 'sensor read'
    global readings
    readings = []
    # value = ADC.read("AIN1")
    # adc returns value from 0 to 1.
    # use read_raw(pin) to get V values
    tank = adc.read(tankPin)
    tank = adc.read(tankPin) # have to read twice due to bbio bug
    print tank
    
    photo = adc.read(photoPin)
    photo = adc.read(photoPin) # have to read twice due to bbio bug
    print photo

    temp1 = adc.read_raw(thermistor1)
    temp1 = adc.read_raw(thermistor1)
    print temp1
    temp1 = convert_thermistor(temp1)
    print temp2
    # do conversion per
    # http://learn.adafruit.com/thermistor/using-a-thermistor

    temp2 = adc.read_raw(thermistor2)
    temp2 = adc.read_raw(thermistor2)
    print temp2
    temp2 = convert_thermistor(temp2)
    print temp2
    # do conversion per
    # http://learn.adafruit.com/thermistor/using-a-thermistor
    # tmp36reading = adc.read_raw(tmp36Pin)
    # tmp36reading = adc.read_raw(tmp36Pin) # have to read twice due to bbio bug
    # millivolts = tmp36reading * 1800  # 1.8V reference = 1800 mV
    # temp_c = (millivolts - 500) / 10
    # print temp_c
    readings.append({'key':'tankLevel','v': tank}) # tank level
    readings.append({'key':'photocell','v': photo}) # photocell
    readings.append({'key':'bed_temp','v':temp1})
    readings.append({'key':'reservoir_temp','v':temp2})

def convert_thermistor(raw):
      # convert the value to resistance
  raw = 1023 / raw - 1
  average = SERIESRESISTOR / average
  print 'Thermistor resistance ' 
  print average
 
  float steinhart
  steinhart = average / THERMISTORNOMINAL     # (R/Ro)
  steinhart = log(steinhart)                  # ln(R/Ro)
  steinhart /= BCOEFFICIENT                   # 1/B * ln(R/Ro)
  steinhart += 1.0 / (TEMPERATURENOMINAL + 273.15) # + (1/To)
  steinhart = 1.0 / steinhart                 # Invert
  steinhart -= 273.15                         # convert to C

def do_db_update():
    print 'db update'
    global readings
    print readings
    if len(readings) != 0:
        client = tempodb.Client(key.API_KEY, key.API_SECRET)
        date = datetime.datetime.now(tzlocal())
        client.write_bulk(date, readings)
        print 'wrote a result set to the DB'
    else:
        print 'NULL readings, nothing written to DB'


def do_state_display():
    print 'state_display'
    # so, what will state display be?
    # I2C display of tank temp?

def do_pump_toggle():
    print 'pump actuate'
    if (datetime.datetime.today().hour>6 and datetime.datetime.today().hour<23):
        print 'within actuating timeframe'
        if(datetime.datetime.today().minute%5 == 0):
            print 'it is a minute that is 0 mod 5, so we start the pump'
            gpio.output(pumpPin,gpio.HIGH)
        else:
            print 'shutting off pump at %s' % datetime.datetime.today().minute
            gpio.output(pumpPin,gpio.LOW)
    else:
        print 'it is the actuator quiet period, between 11pm and 6am'
        gpio.output(pumpPin,gpio.LOW)

print 'starting sampling at'
print datetime.datetime.now(tzlocal())
adc.setup()
gpio.setup(pumpPin,gpio.OUT)
# t = tmp102.TMP102()
# NOTE
# There is currently a bug in the ADC driver.
# You'll need to read the values twice
# in order to get the latest value.
# pwm.start(greenPin, 10.0, 2000.0)
# pwm.start(redPin, 10.0, 2000.0)
# pwm.start(bluePin, 10.0, 2000.0)
atexit.register(exit_handler)

while True:
    try:
        do_sensor_read()
    except:
        print 'sensor_read error!'
    try:
        do_db_update()
    except:
        print 'do_db_update error!'
    try:
        do_state_display()
    except:
        print 'do_state_display error!'
    try:
        do_pump_toggle()
    except:
        print 'do_pump_toggle error!'
    print 'done with cycle, now waiting %s' % datetime.datetime.today()
    time.sleep(interval)