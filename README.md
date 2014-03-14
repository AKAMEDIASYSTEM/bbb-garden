bbb-tempo-garden
================

Beaglebone Black garden monitoring with TempoDB.

Currently does not reliably update to the DB - fails after awhile with a message like "too many connections" (can't recall or access verbatim message right now)

Sensors:
Atlas Scientific pH sensor (38400 baud UART2 connection)
Two NTC 10k thermistors (circuit for one of these is bonkers, yielding temperatures like -69C)
10k analog photocell

Actuators:
20gph pump for reservoir
(possible) dispense pH-altering chemicals?
(possible) dispense nutrients from syringes or other vessels?

Outputs:
(possible) RGB LED strip for temperature history?
(possilbe) OLED or LCD screen with tank level graphic, revervoir temperature, and days-till-nutrient-refresh?
