# Si7005.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# mar 2014 python port of Si7005 arduino library
# AKA

from Adafruit_I2C import Adafruit_I2C
from Adafruit_GPIO import GPIO
import time
from __future__ import division

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

    WAKE_UP_TIME = 0.015 # AKA thinks this was 15ms, so changing it to 0.015sec
    # address
    SI7005_ADR = 0x40


    def __init__(pin):
    	self.i2c = Adafruit_I2C(self.SI7005_ADR)
    	GPIO.setup(pin, GPIO.OUT)
    	GPIO.output(pin,GPIO.HIGH)
    	self._cs_pin = pin

    	self._last_temperature = 25.0
    	self._config_reg = 0
    
    def detectSensor():
        # byte deviceID
        GPIO.output(pin,GPIO.LOW)
        time.sleep(WAKE_UP_TIME)
        # i2c.beginTransmission(self.SI7005_ADR)
        i2c.write8(SI7005_ADR, REG_ID)
        # i2c.endTransmission(false)
        # i2c.requestFrom(SI7005_ADR,1)
        deviceID = i2c.readU8(SI7005_ADR)
        GPIO.output(pin.GPIO.HIGH)
        if (deviceID & ID_SAMPLE) == ID_SI7005:
            return True
        else:
            return False
    
    def doMeasurement(byte configValue):
        GPIO.output(pin, GPIO.LOW) # enable sensor
        time.sleep(WAKE_UP_TIME) # wait for wakeup

        i2c.write8(SI7005_ADR, REG_CONFIG) # select config register
        i2c.write8(SI7005_ADR, (CONFIG_START | configValue | _config_reg)) # Start measurement of the selected type (Temperature / humidity)
        measurementStatus = STATUS_NOT_READY

        while (measurementStatus & STATUS_NOT_READY):
            i2c.write8(SI7005_ADR, REG_STATUS)
            measurementStatus = i2c.readU8(SI7005_ADR)

        i2c.write8(SI7005_ADR, REG_DATA)
        rawData = i2c.readU8(SI7005_ADR) << 8 # MSB
        rawData |= i2c.readU8(SI7005_ADR) # LSB

        GPIO.output(GPIO.HIGH) # disable sensor

        return rawData

    def getTemperature():
    	rawTemperature = self.doMeasurement(CONFIG_TEMPERATURE) >> 2
        _last_temperature = ( rawTemperature / TEMPERATURE_SLOPE ) - TEMPERATURE_OFFSET
        return _last_temperature

    def getHumidity( ):
    	rawHumidity = doMeasurement(CONFIG_HUMIDITY) >> 4
        curve = (rawHumidity / HUMIDITY_SLOPE) - HUMIDITY_OFFSET
        linearHumidity = curve - ( (curve*curve)*a2 + curve*a1 +  a0)
        linearHumidity = linearHumidity + ( _last_temperature - 30 ) * ( linearHumidity * q1 + q0 )
        return linearHumidity

    def enableHeater( ):
    	_config_reg |= CONFIG_HEAT

    def disableHeater( ):
    	_config_reg ^= CONFIG_HEAT

    def enableFastMeasurements( ):
    	_config_reg |= CONFIG_FAST

    def disableFastMeasurements( ):
    	_config_reg ^= CONFIG_FAST