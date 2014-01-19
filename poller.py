
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# jan 2014 bbb garden shield attempt
# AKA
from Adafruit_I2C import Adafruit_I2C
import time
import Adafruit_BBIO.UART as UART
import Adafruit_BBIO.PWM as PWM
import Adafruit_BBIO.GPIO as GPIO
import datetime
import random
from tempodb import Client, DataPoint
import key

# Modify these with your credentials found at: http://tempo-db.com/manage/


client = Client(API_KEY, API_SECRET)