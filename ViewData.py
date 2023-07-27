#!/usr/bin/env python
""" Retrieves data files, if necessary, and prints subplots of potentiometer percentage and distance vs time.

This program is covered under CC BY-SA 4.0. https://creativecommons.org/licenses/by-sa/4.0/

You are free to:

    Share — copy and redistribute the material in any medium or format
    Adapt — remix, transform, and build upon the material
    for any purpose, even commercially.

    This license is acceptable for Free Cultural Works.
    The licensor cannot revoke these freedoms as long as you follow the license terms.

This application is a companion to MonitoringApp.py and is able to download data files from a remote Raspberry pi and
    plot their data. Further description can be found in Potentiometer_Ultrasonic_Monitoring_App.pdf.

Each row of the data file will contain the time stamp and either the potentiometer percentage or the distance.

There are two modes:
    Mode 0 transfers file/s. Mode 1 transfers a file if necessary and then plots the data.

    Usage:
    python ViewData.py 192.168.1.200 0 data200_0412.txt : Transfer file data200_0412.txt from pi to laptop
    python ViewData.py 192.168.1.200 0 : Transfer all data files from /home/pi/Documents/ folder to your machine
    python ViewData.py 192.168.1.200 1 data100_0412.txt :
        If the file exists, plot all sensor data from “data100_0412.txt” using subplots for each sensor data
        If the file does not exist, transfer it from /home/pi/Documents/ and then plot the data.
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
import os
import ipaddress
import os.path
import time
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def valid_ip(addr):
    """
    Determines is a string is a valid IP address

    Parameters
    ----------
    addr : str
        address to check

    Returns
    -------
    bool
        True if addr is a valid IP address, False otherwise
    """

    try:
        # This returns an exception if addr is not a valid IP address
        ipaddress.ip_address(addr)
        return True

    except ValueError:
        print("Invalid IP address...")
        return False


def valid_filename(filename):
    """
    Determines filename is a valid filename with a valid extension

    Parameters
    ----------
    filename : str
        filename to check

    Returns
    -------
    bool
        True if filename is a valid file name, False otherwise
    """
    # Valid extensions
    exts = ['.txt', '.csv']
    root, ext = os.path.splitext(filename)

    if ext not in exts:
        print("Invalid extension...")
        return False
    else:
        return True


def check_arguments():
    """
    Checks number and type of the command line arguments

    Parameters
    ----------
    None.

    Returns
    -------
    bool
        True if the arguments are valid, False otherwise
    """

    # Command line must have either 3 or 4 arguments (with the file name as the first argument)
    if len(sys.argv) != 3 and len(sys.argv) != 4:
        print("Invalid command line argument number",
              "Format: python ViewData.py <ip address> <integer 0 or 1> <filename>")
        return False

    # The second argument must be a valid IP address
    if not valid_ip(sys.argv[1]):
        print("invalid IP address...")
        return False
    # The third argument must be 0 or 1
    elif int(sys.argv[2]) != 0 and int(sys.argv[2]) != 1:
        print("invalid mode...")
        print(sys.argv[2])
        return False

    # If the number of arguments is 3, it must be mode 0
    if len(sys.argv) == 3 and int(sys.argv[2]) == 0:
        # The 2 command line arguments are valid
        return True
    # Only mode 0 can have 3 arguments
    elif len(sys.argv) == 3 and int(sys.argv[2]) == 1:
        print("Filename needed for mode 1...")
        return False
    # If there is one, the 4th argument must be a valid filename
    elif not valid_filename(sys.argv[3]):
        # Else it has 3 command line arguments. Check filename.
        print("invalid filename...")
        return False
    else:
        # The 3 command line arguments are valid
        return True


def plot_data(data):
    """
        Plots two subplots, one of the potentiometer percentage vs. time and one of the distance vs. time

        Parameters
        ----------
        data : DataFrame
            contains the time-stamped potentiometer percentage and distance data
        Returns
        -------
        None.
        """
    # Set number of ticks for the subplots
    num_ticks = 10

    # Give an estimate for time to plot.
    choice = input(f"On my computer, this would take about {int(len(data) / 700)} seconds. Would you like to continue?(y/n) ")
    if choice:
        # Get the column names from data
        column_names = list(data.columns.values)

        # data_1 is the potentiometer percentage
        data_1 = data[column_names[0]]
        data_1.dropna(inplace=True)

        # data_2 is the distance
        data_2 = data[column_names[1]]
        data_2.dropna(inplace=True)

        # Set up plot
        plt.figure()
        x1 = list(data_1.index.values)
        x2 = list(data_2.index.values)

        # Creating plot one
        ax1 = plt.subplot(1, 2, 1)

        plt.plot(x1, data_1, 'r', linewidth=0.5)
        plt.title(column_names[0] + ' vs. Time')
        plt.xlabel('Time')
        plt.ylabel(column_names[0])
        plt.xticks(x1, rotation='vertical')

        # Creating plot two
        ax2 = plt.subplot(1, 2, 2)

        # g is for green color
        plt.plot(x2, data_2, 'g', linewidth=0.5)
        plt.title(column_names[1] + ' vs. Time')
        plt.xlabel('Time')
        plt.ylabel(column_names[1])
        plt.xticks(x2, rotation='vertical')

        # show plot
        ax1.xaxis.set_major_locator(plt.MaxNLocator(num_ticks))
        ax2.xaxis.set_major_locator(plt.MaxNLocator(num_ticks))
        plt.subplots_adjust(bottom = 0.4,wspace=0.4)
        plt.show()

    return


def run_mode(mode, ip, filename):
    """
    Runs the requested mode.

    Mode 0 transfers file/s. Mode 1 transfers a file if necessary and then plots the data.

    Python ViewData.py 192.168.1.200 0 data200_0412.txt : Transfer file data200_0412.txt from pi to laptop
    Python ViewData.py 192.168.1.200 0 : Transfer all data files from /home/pi/Documents/ folder to your machine
    Python ViewData.py 192.168.1.200 1 data100_0412.txt :
        If the file exists, plot all sensor data from “data100_0412.txt” using subplots for each sensor data
        If the file does not exist, transfer it from /home/pi/Documents/ and then plot the data.

    Parameters
    ----------
    mode : int
        mode to run. 0 to transfer files. 1 to plot data. See docstring for more details.
    ip : str
        remote machine's ip address
    filename : str
        name of file to search for. If mode 0, "" denotes all files

    Returns
    -------
    None.

    """

    # Define pi and local paths
    pi_path = Path("/home/pi/Documents/*")
    directory = Path(os.getcwd())
    local_path = Path(directory / "DataFiles")

    # If mode 0 was chosen
    if mode == 0:
        # If the folder doesn't exist, create it
        if not local_path.exists():
            print("Creating directory:", str(local_path))
            os.mkdir('DataFiles')
        # String for scp file transfer command.
        scp_string = "scp pi@" + ip + ":" + str(pi_path) + filename + " " + str(local_path)
        print("Running:", scp_string)
        os.system(scp_string)

    if mode == 1:
        # If the folder doesn't exist, create it
        if not local_path.exists():
            print("Creating directory:", str(local_path))
            os.mkdir('DataFiles')

        # Set path to file
        local_path = local_path / filename

        # Check if file exists locally. If it doesn't, search the remote computer.
        if not os.path.isfile(local_path):
            print(f"{filename} does not exist at {local_path}, searching Pi...")
            scp_string = "scp pi@" + ip + ":" + str(pi_path) + filename + " " + str(local_path)
            print("Running:", scp_string)
            os.system(scp_string)

            # Wait for possible timeout; it is 22 seconds on my computer.
            t0 = time.time()
            while not os.path.isfile(local_path) and t0 < 25:
                pass

            # If the transfer was successful...
            if os.path.isfile(local_path):
                print(f"{filename} retrieved.")
            else:
                print(f"Either {ip} is an invalid IP address or {filename} does not exist locally or remotely.")
                return 0

        print(f"{filename} found. Plotting graph.")

        # Get data from file and plot it
        data = pd.read_csv(local_path, header=0, index_col=0)
        plot_data(data)

        return


def main():
    """
        Main function.

        Parameters
        ----------
        None.

        Returns
        -------
        None.

        """
    # Check the command line arguments.
    if not check_arguments():
        print("Invalid command line arguments.\n"
              "Format: python ViewData.py <ip address> <integer 0 or 1> <filename>")
        sys.exit(0)

    # Get the ip address
    ip = sys.argv[1]
    # Get the mode
    mode = int(sys.argv[2])

    # Get filename if it exists
    if len(sys.argv) == 4:
        filename = sys.argv[3]
    else:
        filename = ""

    # Run the mode
    run_mode(mode, ip, filename)


if __name__ == "__main__":
    main()
