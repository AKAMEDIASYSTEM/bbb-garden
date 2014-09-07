
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

Some measurements as of mid-March 2014:

Tank can be pumped for 15 minutes without sun exposure to liquid.
Seems like after 10 minutes of pumping, the autosiphon engages, though.
Tank takes about 17 minutes to drain from a 15-minute pump

11 gals in reservoir reads as 0.42 on the adc.read scale from 0 to 1
8 gals in reservoir reads as 0.175 on the adc.read scale from 0 to 1
7 gals in reservoir reads as 0.15 on the adc.read scale from 0 to 1
'''
from __future__ import division
import Adafruit_SSD1306 as ssd
import Adafruit_BBIO.UART as uart
import Image
import ImageDraw
import ImageFont
# import Adafruit_GPIO.PWM as pwm
import Adafruit_BBIO.GPIO as gpio
import Adafruit_BBIO.ADC as adc
# import TMP102 as tmp102
import datetime
from dateutil.tz import tzlocal
import time
import serial
import atexit
from math import log
import requests
import key as k

BCOEFFICIENT = 3950 # thermistor beta coefficient
THERMISTORNOMINAL = 10000
TEMPERATURENOMINAL = 25.0
SERIESRESISTOR = 10000
# a1 = blue and white, which is bed temp
# a2 = white and orange, which is tank temp
interval = 60 # seconds between samples
greenPin = 'P8_13'
bluePin = 'P9_14'
redPin = 'P8_19'
servoPin = 'P9_16'
tankPin = 'P9_39'
photoPin = 'P9_38'
thermistor1 = 'P9_40' # AIN1, bed temp
thermistor2 = 'P9_37' # AIN2, reservoir temp
pumpPin = 'P8_10'
RST = 'P8_10' # OLED screen reset pin, not always necessary
readings = {}
PUMP_INTERVAL = 60 # minutes between pump actuations
PUMP_DURATION = 12 # minutes to run pump

def exit_handler():
    print 'exiting'
    gpio.output(pumpPin,gpio.LOW)
    gpio.cleanup()
    uart.cleanup()

def do_sensor_read():
    print 'sensor read'
    global readings
    readings = {}
    # value = ADC.read("AIN1")
    # adc returns value from 0 to 1.
    # use read_raw(pin) to get V values
    tank = adc.read(tankPin)
    tank = adc.read(tankPin) # have to read twice due to bbio bug
    print 'tank is %s' % tank
    time.sleep(3)
    
    
    photo = adc.read(photoPin)
    photo = adc.read(photoPin) # have to read twice due to bbio bug
    print 'photo is %s' % photo
    time.sleep(3)
    

    temp1 = adc.read_raw(thermistor1)
    time.sleep(1)
    temp1 = 1023 - adc.read_raw(thermistor1)
    time.sleep(3)
    print 'temp1 raw %s' % temp1
    temp1 = convert_thermistor(temp1)
    readings['bedTemp'] = temp1
    print 'converted bed_temp is %s' % temp1
    
    # # do conversion per
    # # http://learn.adafruit.com/thermistor/using-a-thermistor

    temp2 = adc.read_raw(thermistor2)
    time.sleep(1)
    temp2 = adc.read_raw(thermistor2)
    time.sleep(3)
    print 'temp2 raw %s' % temp2
    temp2 = convert_thermistor(temp2)
    readings['tankTemp'] = temp2
    print 'converted reservoir_temp is %s' % temp2

    # do conversion per
    # http://learn.adafruit.com/thermistor/using-a-thermistor
    # tmp36reading = adc.read_raw(tmp36Pin)
    # tmp36reading = adc.read_raw(tmp36Pin) # have to read twice due to bbio bug
    # millivolts = tmp36reading * 1800  # 1.8V reference = 1800 mV
    # temp_c = (millivolts - 500) / 10
    # print temp_c

    # ph_val = get_ph()
    # print 'ph_val was thoght to be %s' % ph_val

    readings['tankLevel'] = tank # tank level
    readings['photocell'] = photo # photocell

def convert_thermistor(raw):
    # convert the value to resistance
    # print 'was given %s' % raw
    raw = float(1023 / float(raw)) - 1
    raw = float(SERIESRESISTOR / float(raw))
    print 'Thermistor resistance ' 
    print raw
    steinhart = float(float(raw)/THERMISTORNOMINAL)     # (R/Ro)
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
        # data.sparkfun.com is expecting:
        # bedTemp, photo, tankLevel, tankTemp
        bedTemp = float('{0:.2f}'.format(readings['bedTemp']))
        tankTemp = float('{0:.2f}'.format(readings['tankTemp']))
        payload = {
        'photo':readings['photocell'],
        'tankLevel':readings['tankLevel'],
        'bedTemp':readings['bedTemp'],
        'tankTemp':readings['tankTemp']
        }
        h = {'Phant-Private-Key':k.key['phant_private']}
        r = requests.post(k.key['phant_url'], data=payload, headers=h)
        print 'wrote a result set to the DB'
    else:
        print 'NULL readings, nothing written to DB'

def get_ph():
    print 'we are in get_ph'
    uart.setup('UART2')
    ser = serial.Serial(port = '/dev/ttyO2', baudrate=38400)
    print 'opened serial port'
    ser.open()
    ser.write('R\r')
    data = ser.read()
    print 'ph received raw as %s' % data
    ser.close()
    uart.cleanup()
    return data

def do_state_display():
    print 'state_display'
    width = disp.width
    height = disp.height
    image = Image.new('1', (width, height))

    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)
    # Load default font.
    # font = ImageFont.load_default()
    # Alternatively load a TTF font.
    # Some other nice fonts to try: http://www.dafont.com/bitmap.php
    font = ImageFont.truetype('enhanced_dot_digital-7.ttf', 20)
    # Draw a black filled box to clear the image.
    draw.rectangle((0,0,width,height), outline=0, fill=0)

    # Draw some shapes.
    # First define some constants to allow easy resizing of shapes.
    padding = 2
    shape_width = 20
    top = padding
    bottom = height-padding

    # Move left to right keeping track of the current x position for drawing shapes.
    x = padding

    draw.text((x, top),    'photo: ',  font=font, fill=255)
    draw.text((x, top+20), 'tankLevel: ', font=font, fill=255)
    draw.text((x, top+40), 'tankTemp: ', font=font, fill=255)
    draw.text((x, top+60), 'bedTemp: ', font=font, fill=255)
    draw.text((x+32, top),    str(readings['photocell']),  font=font, fill=255)
    draw.text((x+32, top+20), str(readings['tankLevel']), font=font, fill=255)
    draw.text((x+32, top+40), str(readings['tankTemp']), font=font, fill=255)      

    # Draw an ellipse.
    # draw.ellipse((x, top , x+shape_width, bottom), outline=255, fill=0)
    # x += shape_width+padding
    # Draw a rectangle.
    # draw.rectangle((x, top, x+shape_width, bottom), outline=255, fill=0)
    # x += shape_width+padding
    # Draw a triangle.
    # draw.polygon([(x, bottom), (x+shape_width/2, top), (x+shape_width, bottom)], outline=255, fill=0)
    # x += shape_width+padding
    # Draw an X.
    # draw.line((x, bottom, x+shape_width, top), fill=255)
    # draw.line((x, top, x+shape_width, bottom), fill=255)
    # x += shape_width+padding
    draw.text((x+32, top+60), str(readings['bedTemp']), font=font, fill=255)

    # Display image.
    disp.image(image)
    disp.display()
    # so, what will state display be?
    # I2C display of tank temp?

def do_pump_toggle():
    print 'pump actuate'
    '''
    this should actually work like:
    if currentMinute mod PUMP_DURATION < PUMP_INTERVAL:
        activate pump
    else:
        turn off pump
    '''
    if (datetime.datetime.today().hour>6 and datetime.datetime.today().hour<23):
        print 'within actuating timeframe'
        # changed this to just pump for the first PUMP_DURATION minutes every hour
        if(datetime.datetime.today().minute <= PUMP_DURATION):
            print 'we are in the first %s minutes of the hour, so pump should be on.' % PUMP_INTERVAL
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
# uart.setup('UART2')
# print 'uart setup'
gpio.setup(pumpPin,gpio.OUT)
# t = tmp102.TMP102()
disp = ssd.SSD1306_128_64(rst=RST,i2c_address=0x3D)
disp.begin()
disp.clear()
disp.display()
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
        pass
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
