
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
from __future__ import division
from Adafruit_I2C import Adafruit_I2C
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

interval = 60 # seconds between samples
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
    # pwm.stop(greenPin)
    # pwm.stop(redPin)
    # pwm.stop(bluePin)
    # pwm.stop(servoPin)
    # pwm.cleanup()
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
    time.sleep(1)
    tank = adc.read(tankPin) # have to read twice due to bbio bug
    time.sleep(3)
    print 'tank is %s' % tank
    
    photo = adc.read(photoPin)
    time.sleep(1)
    photo = adc.read(photoPin) # have to read twice due to bbio bug
    time.sleep(3)
    print 'photo is %s' % photo

    temp1 = adc.read_raw(thermistor1)
    time.sleep(1)
    temp1 = adc.read_raw(thermistor1)
    time.sleep(3)
    print 'temp1 raw %s' % temp1
    temp1 = convert_thermistor(temp1)
    print 'converted bed_temp is %s' % temp1
    # do conversion per
    # http://learn.adafruit.com/thermistor/using-a-thermistor

    temp2 = adc.read_raw(thermistor2)
    time.sleep(1)
    temp2 = adc.read_raw(thermistor2)
    time.sleep(3)
    print 'temp2 raw %s' % temp2
    temp2 = convert_thermistor(temp2)
    print 'converted reservoir_temp is %s' % temp2
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
    # print 'was given %s' % raw
    raw = float(1023 / raw) - 1
    raw = float(SERIESRESISTOR / raw)
    print 'Thermistor resistance ' 
    print raw
    steinhart = float(raw/THERMISTORNOMINAL)     # (R/Ro)
    steinhart = log(steinhart)                  # ln(R/Ro)
    steinhart /= BCOEFFICIENT                   # 1/B * ln(R/Ro)
    steinhart += float(1.0 / (TEMPERATURENOMINAL + 273.15)) # + (1/To)
    steinhart = float(1.0 / steinhart)                 # Invert
    steinhart -= 273.15                         # convert to C
    # print 'we think converted temperature is %s' % steinhart
    return steinhart

def do_db_update():
    print 'db update'
    global readings
    # print readings
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
    '''
    this should actually work like:
    if currentMinute mod PUMP_INTERVAL < PUMP DURATION:
        activate pump
    else:
        turn off pump
    '''
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
uart..setup('UART2')
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
    except Exception, e:
        print e
        print 'sensor_read error!'
    try:
        do_db_update()
    except Exception, e:
        print e
        print 'do_db_update error!'
    try:
        do_state_display()
    except Exception, e:
        print e
        print 'do_state_display error!'
    try:
        do_pump_toggle()
    except Exception, e:
        print e
        print 'do_pump_toggle error!'
    print 'done with cycle, now waiting %s' % datetime.datetime.today()
    time.sleep(interval)
