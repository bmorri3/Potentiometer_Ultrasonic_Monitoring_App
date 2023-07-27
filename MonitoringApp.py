#TODO: Create proper README.txt
#TODO: Rename README.txt
#TODO: Proper file header

#!/usr/bin/env python
""" Controls a Pi to collect potentiometer and ultrasonic data while giving options to monitor and record the data.

This program is covered under CC BY-SA 4.0. https://creativecommons.org/licenses/by-sa/4.0/

You are free to:

    Share — copy and redistribute the material in any medium or format
    Adapt — remix, transform, and build upon the material
    for any purpose, even commercially.

    This license is acceptable for Free Cultural Works.
    The licensor cannot revoke these freedoms as long as you follow the license terms.
    
This program uses a Raspberry pi to detect the percentage that a potentiometer is turned (every 0.5 seconds) and distance from an
    unltrasonic sensor (every 0.1 seconds). Further description, including GPIO pin numbers, can be found in the assignment documentation.

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
"""

__author__ = "Ben Morris"
__copyright__ = "Copyright 2023"
__credits__ = "Ben Morris"
__license__ = "CC BY-SA 4.0"
__version__ = "1.0.1"
__maintainer__ = "Ben Morris"
__email__ = "benjaminclaymorris@gmail.com"
__status__ = "Production"


import sys
import os.path    
import time

import pandas as pd
import RPi.GPIO as gpio

from datetime import datetime
from gpiozero import MCP3008
from gpiozero import RGBLED
from gpiozero import Button
from gpiozero import LED

# Use BCM pins
gpio.setmode(gpio.BCM)

# Interval for beep on/off
BEEP_INTERVAL = 0.5

# Pin number for the button
BUTTON = 16

# Pin number for the buzzer
BUZZER = 18

# Pin numbers for the ultrasonic sensor
ECHO = 24
TRIG = 25

# Set up the GPIO pins
gpio.setup(BUZZER, gpio.OUT)
gpio.setup(ECHO, gpio.IN)
gpio.setup(TRIG, gpio.OUT, initial=gpio.LOW)
gpio.setup(BUTTON, gpio.IN, pull_up_down=gpio.PUD_UP)
gpio.setwarnings(False)

# Use gpiozero for the LEDs
rgbled = RGBLED(5, 6, 13, active_high = True)
regled = LED(14)
regled.off()

# Offesets to maintain proper timing
SONIC_OFFSET = 0.088
POT_OFFSET = 0.492

# Buzzer setting
DUTY_CYCLE = 10

# Min and max for distance and buzzer sounds
MIN_DIST = 4
MAX_DIST = 20
MIN_FREQ = 100
MAX_FREQ = 2000

# Conversion rate for potentiometer percentage to match red->violet on the LED
VIOLET_RATIO = 0.75

# Buffer size before writing the file
BUFFER_SIZE = 250

# Time to double-click for RDM
RDM_TIME = 1
# Time to hold for ORD
ORD_TIME = 2

# Mode numbers
MS_MODE = 1
RDM_MODE = 2
ORD_MODE = 3

# Rate to convert ultrasonic reading to distance in cm
ULTRASONIC_CONVERSION = 79

# Declaring BUTTON with bpiozero
button = Button(BUTTON)

# Global variable for the buzzer
buzz = gpio.PWM(BUZZER, 1)

# Global variable for the current mode, initialized to MS
mode = MS_MODE

def sonic():
    """
    Uses the ultrasonic sensor to return distance.
    
    Parameters
    ----------
    None.

    Returns
    -------
    dtime : datetime
        Time that the measurement was taken
    distance : float
        Object's distance from the ultrasonic sensor
    """
    
    # Initialize variables
    distance = 0.0
    dtime = time.time()

    try:
        # To detect change in modes
        old_mode = mode
        
        # Turn trigger on and off
        gpio.output(TRIG, True)
        time.sleep(0.00001)
        gpio.output(TRIG, False)
        
        # Initialize times for start and end of pulse and duration
        pulse_start = 0.0
        pulse_end = 0.0    
        pulse_duration = -1.0
        
        # Make sure the duration is positive and mode hasn't changed
        while pulse_duration <= 0 and old_mode == mode:
            while gpio.input(ECHO)==0 and old_mode == mode:
                pulse_start = time.time()              #Saves the last known time of LOW pulse
            
            while gpio.input(ECHO)==1 and old_mode == mode:               #Check whether the ECHO is HIGH
                pulse_end = time.time()                #Saves the last known time of HIGH pulse
        
            pulse_duration = (pulse_end - pulse_start)*1000000 #Get pulse duration to a variable in uS
        
        # Set dtime to now
        dtime = time.time()

        # Divide pulse duration by ULTRASONIC_CONVERSION to get distance
        # Theoretically, this was supposed to be 58, but I had to make it 79 for my device to measure accurately.
        distance = pulse_duration / ULTRASONIC_CONVERSION       
        distance = round(distance, 2)       

    except KeyboardInterrupt:
        print("Sonic measurement stopped by User")
        return dtime, distance

    return dtime, distance


def frequency(distance):
    """    
    Uses the ultrasonic sensor to return distance.
    
    Parameters
    ----------
    distance : float
        distance of object to ultrasonic sensor in cm

    Returns
    -------
    freq : float
        Frequency of buzzer based on distance
    """
 
    # Set frequency based on distance
    if distance > MAX_DIST:
        freq = None
    elif distance < MIN_DIST:
        freq = MAX_FREQ
    else:
        # Frequency (MIN_FREQ to MAX_FREQ is proportional to the distance from MIN_DIST to MAX_DIST
        freq_proportion = (distance - MIN_DIST) / (MAX_DIST - MIN_DIST)
        if distance <= MAX_DIST and distance >= MIN_DIST:
            freq = MAX_FREQ - freq_proportion * (MAX_FREQ - MIN_FREQ)    
    
    return freq


def buzzer(distance):
    """
    Changes the buzzer based on the distance.
    Frequency (MIN_FREQ to MAX_FREQ is proportional to the distance from MIN_DIST to MAX_DIST
    
    Parameters
    ----------
    distance : float
        distance of object to ultrasonic sensor in cm

    Returns
    -------
    freq : float
        Frequency of buzzer based on distance
    """
    # Get the frequency
    freq = frequency(distance)
    
    # If the frequency is not None, change the frequency of the buzzer
    if freq:
        buzz.ChangeFrequency(freq)
        
    # Start the new freqency
    buzz.start(DUTY_CYCLE)
    
    return freq


def in_range(distance):
    """
    Returns True if distance is between MIN_DIST and MAX_DIST, inclusive. Return False otherwise.
    
    Parameters
    ----------
    distance : float
        distance of object to ultrasonic sensor in cm

    Returns
    -------
    bool
        Returns True if distance is between MIN_DIST and MAX_DIST, inclusive. Return False otherwise.
    """
    if distance >= MIN_DIST and distance <= MAX_DIST:
        return True
    else:
        return False


def get_color(percent):   
    """
    Piecewise RGB determination based on the linear approximations shown here: https://stackoverflow.com/questions/8507885/shift-hue-of-an-rgb-color
    
    Parameters
    ----------
    percent : float
        Potentiometer percentage between 0 and 100

    Returns
    -------
    red, green, blue
        RGB values between 0 and 255. The combinations of these colors will determine the color of the color LED
    """
    
    # The piecewise function goes further than violet. This ratio stops the LED at VIOLET (127, 0, 255)
    percent = percent * VIOLET_RATIO

    
    if percent <= 100 * 1/6:
        red = 1
        green = percent / (100 * 1/6)
        blue = 0
        
    elif 100 * 1/6 < percent <= 100 * 2/6:
        red = 1 - (percent - 100 * 1/6)/(100 * 1/6)
        green = 1
        blue = 0
        
    elif 100 * 2/6 < percent <= 100 * 3/6:
        red = 0
        green = 1
        blue = (percent - 100 * 2/6) / (100 * 1/6)
        
    elif 100 * 3/6 < percent <= 100 * 4/6:
        red = 0
        green = 1 - (percent - 100 * 3/6) / (100 * 1/6)
        blue = 1
        
    elif 100 * 4/6 < percent <= 100 * 5/6:
        red = (percent - 100 * 4/6)/(100 * 1/6)
        green = 0
        blue = 1
        
    elif percent > 5/6:
        red = 1
        green = 0
        blue = 1 - (percent - 100 * 5/6) / (100 * 1/6)
    
    return red, green, blue


def mode_settings(cmode):
    """
    Get the settings for monitor and record based on the mode.
    
    Mode 1 (MS): monitor = True, record = False
    Mode 2 (RDM): monitor = True, record = True
    Mode 3 (ORD): monitor = False, record = True
    
    Parameters
    ----------
    mode : int
        1 = MS, 2 = RDM, 3 = ORD

    Returns
    -------
    monitor : bool
        True if monitor is active for the mode, False otherwise
        
    record : bool
        True if record is active for the mode, False otherwise
    """
    
    monitor = False
    record = False
    
    if cmode == 1:
        monitor = True
        record = False
    if cmode == 2:
        monitor = True
        record = True
    if cmode == 3:
        monitor = False
        record = True
    
    return monitor, record


def append_data(data, filename):
    """
    Helper function to append the data to the csv filename
        
    Parameters
    ----------
    data : DataFrame
        Buffered data including date_time, potentiometer percentage, and distance
        
    filename : str
        Name of file to append
        
    Returns
    -------
    None.
    
    """
    
    # If the file exists, append the file
    if os.path.isfile(filename):
        data.to_csv(filename, mode="a", index=False)
    else:
        print(f"{filename} does not exist. Exiting program.")
        sys.exit(-1)


def get_mode(t0=-1):   
    """
    Helper function to get mode based on button clicks.
        
    Parameters
    ----------
    t0 : time.time()
        Initial time of button press. Initialized to -1.    
        
    Returns
    -------
    None.
    
    """
    
    # Global variable for current mode
    global mode
    
    try:
        # The button should already  be pressed when entering the function.
        if button.is_pressed:
            # If time hasn't been initialized, do it.
            if t0 == -1:
                t0 = time.time()

            #print("Button Pressed")
        
            # While BUTTON is pressed, wait RDM_TIME seconds while checking for BUTTON to be released.
            while time.time() - t0 <= RDM_TIME:
                # If BUTTON is released, check for a second press
                if not button.is_pressed: 
                    while time.time() - t0 <= RDM_TIME:
                        # If the button is pressed a second time, check for releasing within RDM_TIME from t0
                        if button.is_pressed:
                            t1 = time.time()
                            while time.time() - t0 <= RDM_TIME:
                                if not button.is_pressed:
                                    # If the mode has changed, change the mode.
                                    if mode != RDM_MODE:
                                        print("RDM mode")
                                        mode = RDM_MODE # Mode 2: RDM mode
                                        regled.on()
                                    return
                            # If the button wasn't released in time, change to MS mode and start the function over
                            print("MS mode")
                            mode = MS_MODE
                            regled.off()
                            get_mode(t1)
                            return
                    # If the mode has changed, change the mode.
                    if mode != MS_MODE:    
                        print("MS mode")
                        mode = MS_MODE # Mode 1: MS Mode
                        regled.off()
                    return                
            
            # If the button hasn't been released yet, check for ORD
            while time.time() - t0 <= ORD_TIME:
                # If the button is released
                if not button.is_pressed:
                    # If the mode has changed, change the mode.
                    if mode != MS_MODE:
                        print("MS mode")
                        mode = MS_MODE # Mode 1: MS Mode
                        regled.off()
                    return
            # If BUTTON is still pressed after ORD_TIME seconds, set mode to ORD_MODE and return    
            if mode != ORD_MODE:                
                print("ORD Mode")
                mode = ORD_MODE
                regled.blink()
            return
        
    except KeyboardInterrupt:
        print("get_mode() stopped by User")
        return


def run_mode():
    """
    Function to run the code based on the mode.
        
    Parameters
    ----------
    None.  
        
    Returns
    -------
    None.
    
    """   
    try:
        while True:
            # Initialize to check for mode change
            old_mode = mode

            # Begin with buzzer off
            buzz.stop()

            # Initialize distance and rgb timers
            dist_t0 = time.time()
            rgb_t0 = dist_t0
            
            # Set up potentiometer
            pot = MCP3008(channel=0)
            # Get initial potentiometer percent
            pot_percent = round(pot.value * 100, 2)            
            # Get initial color based on the potentiometer percent
            R, G, B = get_color(pot_percent)        
                    
            # Get settings for monitor and record based on mode
            monitor, record = mode_settings(mode)            
            
            # Get the current date and time for filename.
            time_string = str(time.ctime())
            time_string = time_string[4:7] + time_string[8:10] + time_string[20:24] + "_" + time_string[11:13] + time_string[14:16] + time_string[17:19] + ".csv"
            filename = "//home//pi/Documents//data_" + time_string
            
            # Get header for file
            header = pd.DataFrame(columns=['Date and Time', 'Potentiometer %', 'Distance'])
            
            # If record is active, write the header to the file 
            if record:
                header.to_csv(filename, mode="a", index = False)
                print(f"Recording data to {filename}...")
            
            # If monitor mode, turn on the light
            if monitor:             
                rgbled.color = (R, G, B)            
            
            # Initialize DataFrame to collect data
            data = pd.DataFrame(columns=['Date and Time', 'Potentiometer %', 'Distance'])
            
            # Initialize too_close to False
            too_close = False
            
            # While the mode hasn't changed
            while old_mode == mode:
                # While the time is less than the time between ultrasonic readings
                while time.time() - dist_t0 < SONIC_OFFSET:
                    # If it has been longer than the time between potentiometer readings...
                    if time.time() - rgb_t0 > POT_OFFSET:
                        
                        # Get the potentiometer value and convert it to a percent
                        value = pot.value                    
                        pot_percent = round(value * 100, 2)
                        
                        # Initialize the rgb timer.
                        rgbtime = time.time()
                        
                        # Convert the rgb reading time to datetime
                        date_time = datetime.fromtimestamp(rgbtime).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

                        # Change color LED
                        R, G, B = get_color(pot_percent)        
                        rgbled.color = (R, G, B)
                        
                        # Convert to 0->255 for monitoring and recording purposes.
                        R = int(R*255)
                        G = int(G*255)
                        B = int(B*255)

                        # If monitoring, print to console
                        if monitor:
                            print(f"Date and Time: {date_time}, Potentiometer %: {pot_percent}, RGB: ({R}, {G}, {B})")
                        
                        # Create a new line of data
                        new_data = {'Date and Time': date_time, 'Potentiometer %': pot_percent, 'Distance': 'NaN'}
                        new_data = pd.DataFrame.from_dict([new_data])
                        
                        # If recording, at the data to the DataFrame
                        if record:
                            data = pd.concat([data, new_data], ignore_index=True, sort=False)
                        
                        # Reset rgb timer
                        rgb_t0 = time.time()
                        
                # Get time and distance from the ultrasonic sensor               
                dtime, distance = sonic()
                
                # Convert distance to frequency and change buzzer
                freq = frequency(distance)
                if freq:
                    freq = int(freq)
                    buzz.ChangeFrequency(freq)
                
                # If monitoring...
                if monitor:
                    # Determine what to do with the buzzer
                    
                    # If farther than MAX_DIST, stop the buzzer
                    if distance > MAX_DIST:
                        buzz.stop()
                        too_close = False
                    
                    # If in range, start the buzzer
                    elif in_range(distance):                                    
                        buzz.start(DUTY_CYCLE)
                        too_close = False
                    
                    # Must be closer than MIN_DIST, so set the flag for the first iteration and initalize the beep timer.
                    # Next iteration will run the beeping buzzer.
                    elif not too_close:
                        # Set flag
                        too_close = True
                        # Initialize beep timer
                        beep_t0 = dist_t0
                    # It is closer than MIN_DIST, so start the beeping
                    else:
                        # Stop the buzzer
                        buzz.stop()
                        # Change the frequency
                        buzz.ChangeFrequency(MAX_FREQ)
                        # Start the buzzer
                        buzz.start(DUTY_CYCLE)

                        # If the distance is still too close and the mode hasn't changed
                        if distance < MIN_DIST and old_mode == mode:                        
                            
                            # If the time beep interval has passed, stop the buzzer
                            if time.time() > beep_t0 + BEEP_INTERVAL and distance < MIN_DIST and old_mode == mode:
                                buzz.stop()
                            
                            # If another beep interval has passed, start the buzzer and reset the buzzer timer
                            if time.time() > beep_t0 + 2 * BEEP_INTERVAL and distance < MIN_DIST and old_mode == mode:
                                beep_t0 = beep_t0 + 2 * BEEP_INTERVAL
                                buzz.start(DUTY_CYCLE)
                                buzz.ChangeFrequency(MAX_FREQ)
                
                #date_time = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                date_time = datetime.fromtimestamp(dtime).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                
                # If the distance is more than a meter, ignore it.
                if distance > 100:
                    distance = 'NaN'
                new_data = {'Date and Time': date_time, 'Potentiometer %': 'NaN', 'Distance': distance}
                new_data = pd.DataFrame.from_dict([new_data])
                
                # If recording, update DataFrame
                if record:
                    data = pd.concat([data, new_data], ignore_index=True, sort=False)
                # If monitoring, print the distance data
                if monitor:
                    print(f"Date and Time: {date_time}, Distance: {distance}, freq: {freq}")

                # Convert dtime
                date_time = datetime.fromtimestamp(dtime).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]                                                
                  
                # If the buffer size has been reached, write the file and clear the buffer.
                if data.index.size > BUFFER_SIZE:
                    print("Writing buffer...")
                    
                    # Arrange the data
                    data = data[['Date and Time', 'Potentiometer %', 'Distance']]
                    # Sort the data
                    data.sort_values(by=['Date and Time'], inplace=True)
                    # Get rid of the first column
                    data = data[data.columns[1:]]
                    # Write file
                    data.to_csv(filename, mode="a", index=False, header=False)               
                    # Clear buffer
                    data = pd.DataFrame()

                # Reset distance timer
                dist_t0 = time.time()

            # Stop the buzzer
            buzz.stop()

            # Re-format the DataFrame
            data = data[['Date and Time', 'Potentiometer %', 'Distance']]
            data.sort_values(by=['Date and Time'], inplace=True)
            data = data.reset_index()
            data = data[data.columns[1:]]
            
            # Writing anything remaining in the buffer.
            if record:
                print("Writing buffer...")                
                data.to_csv(filename, mode="a", index=False, header=False)
                print(f"Stopped recording data to {filename}...")

            
    except KeyboardInterrupt:
        print("Run_mode() stopped by User")
        # If recording, write what is in the buffer.
        if record:
            print("Writing buffer...")
            # Reformat the DataFrame
            data = data[['Date and Time', 'Potentiometer %', 'Distance']]
            data.sort_values(by=['Date and Time'], inplace=True)
            data = data.reset_index()
            data = data[data.columns[1:]]
            
            # Write the data
            data.to_csv(filename, mode="a", index=False, header=False)
            print(f"Stopped recording data to {filename}...")

        return


def main():
    """
    Main function
        
    Parameters
    ----------
    None.  
        
    Returns
    -------
    None.
    
    """ 
    try:
        # Global variable for the current mode
        global mode
        
        mode = MS_MODE # Default

        # Create a event handler for when the button is pressed
        button.when_pressed = get_mode
                
        # Run the main function for handling the current mode
        run_mode()

    except KeyboardInterrupt:
        print("Main() stopped by User")
        
        # Clean up the pins
        gpio.cleanup()
        sys.exit(1)
        

if __name__ == "__main__":
    main()


