# Si7005.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# mar 2014 python port of Si7005 arduino library
# AKA
from __future__ import division
from Adafruit_I2C import Adafruit_I2C
import Adafruit_BBIO.GPIO as GPIO
import time


class si7005():
    # /* Si7005 Registers */
    REG_STATUS         = 0x00
    REG_DATA           = 0x01
    REG_CONFIG         = 0x03
    REG_ID             = 0x11

    # /* Status Register */
    STATUS_NOT_READY   = 0x01

    # /* Config Register */
    CONFIG_START       = 0x01
    CONFIG_HEAT        = 0x02
    CONFIG_HUMIDITY    = 0x00
    CONFIG_TEMPERATURE = 0x10
    CONFIG_FAST        = 0x20

    # /* ID Register */
    ID_SAMPLE          = 0xF0
    ID_SI7005          = 0x50

    # /* Coefficients */
    TEMPERATURE_OFFSET  =  50
    TEMPERATURE_SLOPE   =  32
    HUMIDITY_OFFSET     =  24
    HUMIDITY_SLOPE      =  16
    a0 = (-4.7844)
    a1 =  0.4008
    a2 = (-0.00393)
    q0 =  0.1973
    q1 =  0.00237

    WAKE_UP_TIME = 0.15 # AKA thinks this was 15ms, so changing it to 0.015sec
    # address
    SI7005_ADR = 0x40


    def __init__(self,pin):
    	self.i2c = Adafruit_I2C(self.SI7005_ADR)
    	GPIO.setup(pin, GPIO.OUT)
    	GPIO.output(pin,GPIO.HIGH)
    	self._cs_pin = pin

    	self._last_temperature = 25.0
    	self._config_reg = 0
    
    def detectSensor(self):
        # byte deviceID
        GPIO.output(self._cs_pin, GPIO.LOW)
        time.sleep(self.WAKE_UP_TIME)
        # i2c.beginTransmission(self.SI7005_ADR)
        # self.i2c.write8(self.SI7005_ADR, self.REG_ID)
        # i2c.endTransmission(false)
        # i2c.requestFrom(SI7005_ADR,1)
        deviceID = self.i2c.readU8(self.SI7005_ADR)
        GPIO.output(self._cs_pin, GPIO.HIGH)
        if (deviceID & self.ID_SAMPLE) == self.ID_SI7005:
            return True
        else:
            return False
    
    def doMeasurement(self,configValue):
        GPIO.output(self._cs_pin, GPIO.LOW) # enable sensor
        time.sleep(self.WAKE_UP_TIME) # wait for wakeup

        self.i2c.write8(self.SI7005_ADR, self.REG_CONFIG) # select config register
        self.i2c.write8(self.SI7005_ADR, (self.CONFIG_START | configValue | self._config_reg)) # Start measurement of the selected type (Temperature / humidity)
        measurementStatus = self.STATUS_NOT_READY

        while (measurementStatus & self.STATUS_NOT_READY):
            self.i2c.write8(self.SI7005_ADR, self.REG_STATUS)
            measurementStatus = self.i2c.readU8(self.SI7005_ADR)

        self.i2c.write8(self.SI7005_ADR, REG_DATA)
        rawData = self.i2c.readU8(self.SI7005_ADR) << 8 # MSB
        rawData |= self.i2c.readU8(self.SI7005_ADR) # LSB

        GPIO.output(self._cs_pin, GPIO.HIGH) # disable sensor

        return rawData

    def getTemperature(self):
    	rawTemperature = self.doMeasurement(self.CONFIG_TEMPERATURE) >> 2
        _last_temperature = ( rawTemperature / self.TEMPERATURE_SLOPE ) - self.TEMPERATURE_OFFSET
        return _last_temperature

    def getHumidity( self):
    	rawHumidity = doMeasurement(self.CONFIG_HUMIDITY) >> 4
        curve = (rawHumidity / self.HUMIDITY_SLOPE) - self.HUMIDITY_OFFSET
        linearHumidity = curve - ( (curve*curve)*a2 + curve*a1 +  a0)
        linearHumidity = linearHumidity + ( _last_temperature - 30 ) * ( linearHumidity * q1 + q0 )
        return linearHumidity

    def enableHeater(self ):
    	_config_reg |= CONFIG_HEAT

    def disableHeater(self ):
    	_config_reg ^= CONFIG_HEAT

    def enableFastMeasurements(self ):
    	_config_reg |= CONFIG_FAST

    def disableFastMeasurements(self ):
    	_config_reg ^= CONFIG_FAST