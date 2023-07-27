# MonitoringApp.py and ViewData.py

### Potentiometer and Ultrasonic Sensor Monitoring and Recording Application

### MonitoringApp.py Description
MonitoringApp.py uses a Raspberry pi to detect the percentage that a potentiometer is turned (every 0.5 seconds) and 
    the distance from an unltrasonic sensor (every 0.1 seconds). ViewData.py runs on a remote computer. It retrieves 
    the recorded data files from the Raspberry Pi and plots the data.

Further description, including GPIO pin numbers, can be found in Potentiometer_Ultrasonic_Monitoring_App.pdf.

There are three modes:

MS: Monitor System
    A buzzer sounds depending on the distance that the ultrasonic sensor reads. From 4 cm to 20 cm, the frequency
        changes from 2 KHz to 100 Hz. If farther than 20 cm, there is no buzzer. If closer than 4 cm, the buzzer
        beeps at 2 KHz (on and off for 0.5 seconds each).
    As the potentiometer goes from 0 to 100%, a color led changes from Red to Violet across the visible spectrum.
    The regular led is off.
    The statuses of the potentiometer and the ultrasonic sensor are printed to the console.
    
RDM: Record Data and Monitor
    All of the behaviors of MS, plus the data will be recorded to a file with the date and time as the filename.
    The regular led is on.
    
ORD: Only Record Data
    The system will not be monitored (i.e. buzzer off, color led off, and no updates printed to the console).
    The regular led will blink (on and off for 1 second each).
    
Each row of the data file will contain the time stamp and either the potentiometer percentage or the distance.

The code is mostly modularized, but could benefit from a little cleanup in run_mode(). Use of OOP could be considered
    as well.

### MonitoringApp.py Description
Retrieves data files, if necessary, and prints subplots of potentiometer percentage and distance vs time.

The application downloads data files from a remote Raspberry pi and plot their data.

There are two modes:
Mode 0 transfers file/s. Mode 1 transfers a file if necessary and then plots the data.

Usage:
    python ViewData.py 192.168.1.200 0 data200_0412.txt : Transfer file data200_0412.txt from pi to laptop
    python ViewData.py 192.168.1.200 0 : Transfer all data files from /home/pi/Documents/ folder to your machine
    python ViewData.py 192.168.1.200 1 data100_0412.txt :
        If the file exists, plot all sensor data from “data100_0412.txt” using subplots for each sensor data
        If the file does not exist, transfer it from /home/pi/Documents/ and then plot the data.


## Installation
Not applicable


## Usage
### On the Raspberry Pi
```
python

import MonitoringApp.py

# Runs the program
python MonitoringApp.py

```
Notes: My ultrasonic sensor needed a different calibration than what literature usually says. It needed to be divided
by 79 instead of 58. If the distance of the ultrasonic sensor is off, change the variable ULTRASONIC_CONVERSION.

### On the remote computer
```
python

import ClientData.py

python ClientData.py <Pi's IP address> <mode> <optional: filename>


## License

This program is covered under CC BY-SA 4.0. https://creativecommons.org/licenses/by-sa/4.0/

You are free to:

    Share — copy and redistribute the material in any medium or format
    Adapt — remix, transform, and build upon the material
    for any purpose, even commercially.

    This license is acceptable for Free Cultural Works.
    The licensor cannot revoke these freedoms as long as you follow the license terms.



