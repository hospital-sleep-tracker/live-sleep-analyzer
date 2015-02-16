"""
Shared library of classes for sleep logging, analyzing, and graphing
"""
import re, time, sys, glob, os, csv, datetime, argparse
import serial, usb
from ftplib import FTP
import logging as log

import numpy
from matplotlib import pyplot, animation

from credentials import DIGITAL_OCEAN_IP, USER, PASSWD

ONE_MEGABYTE = 1000000

log.basicConfig(level=log.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')

def upload_new_logfiles():
  # Make sure we're in the right directory
  if (os.getcwd() != os.path.dirname(os.path.realpath(__file__))):
    log.error("Please cd into the script directory before running it!")
    sys.exit(1)

  # Setup FTP
  ftp = FTP(timeout=5)
  ftp.connect(DIGITAL_OCEAN_IP)
  ftp.login(USER, PASSWD)
  ftp.cwd('logs')

  sleep_logfiles = glob.glob('./logs/*.slp.csv')
  if len(sleep_logfiles) > 0:
    for sleep_logfile in sleep_logfiles:
      if os.stat(sleep_logfile).st_size > ONE_MEGABYTE:
        # Check if file is already on the server
        sleep_logfile_name = os.path.basename(sleep_logfile)
        files_on_server = []
        ftp.retrlines('LIST %s' % sleep_logfile_name, files_on_server.append)

        # If not, upload it
        if len(files_on_server) == 0:
          opened_sleep_logfile = open(sleep_logfile)
          transfer_cmd = 'STOR %s' % sleep_logfile_name
          ftp.storbinary(transfer_cmd, opened_sleep_logfile)

      # Remove it
      os.remove(sleep_logfile)

  ftp.close()

class Analyzer(object):
    def __init__(self):
        self.values = []
        self.rem_sleep = True

    def add(self, value):
        self.values.append(value)

    @property
    def num_values_recorded(self):
        return len(self.values)


class LightSwitch(object):
    """Used to turn the raspberry pi indicator light on and off.
    The class is necessary to hold state of whether the light is currently on or off.
    It is much faster to save state then do an arbitrary hardware write every time.
    """
    def __init__(self):
        self._is_on = False

    def turn_on(self):
        """Turns the light on, ONLY if it is currently off"""
        if not self._is_on:
            try:
                with open('/sys/class/leds/ACT/brightness', 'w') as f:
                    f.write('1')
                self._is_on = True
            except IOError:
                log.warning("Unable to change indicator led")

    def turn_off(self):
        """Turns the ligh off, ONLY if it is currently on"""
        if self._is_on:
            try:
                with open('/sys/class/leds/ACT/brightness', 'w') as f:
                    f.write('0')
                self._is_on = False
            except IOError:
                log.warning("Unable to change indicator led")


class Graph(object):
    """Graphs data as it is supplied"""
    def __init__(self):
        pyplot.ion()
        self.data = [0] * 50
        self.ax = pyplot.axes(xlim=(0, 50), ylim=(0, 200))
        self.line, = self.ax.plot(self.data, lw=2)

    def add(self, movement_value):
        self.data.append(movement_value)
        del self.data[0]
        self.line.set_data(range(0,50), self.data)
        pyplot.draw()

    def show(self):
        pass


class LazyGraph(object):
    def __init__(self):
        pyplot.ion()
        self.data = []
        self.ax = pyplot.axes(xlim=(0, 50), ylim=(0, 200))
        self.line, = self.ax.plot(self.data, lw=2)

    def add(self, movement_value):
        self.data.append(movement_value)

    def show(self):
        pyplot.ylim((0, 200))
        pyplot.xlim((0, len(self.data)))
        self.line.set_data(range(0,len(self.data)), self.data)
        pyplot.draw()


class InputDevice(object):
    def __init__(self, filename):
        pass

    def get_next_movement_value(self):
        raise NotImplementedError()

    def is_ready(self):
        return True


class Teensy(InputDevice):
    def __init__(self):
        self.teensy = None
        """Serial object"""

        while self.teensy is None:
            self.teensy = self._get_teensy_usb()

    def _get_teensy_usb(self):
        """Searches, opens, and returns a serial port object connected to the teensy

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            An initialized serial object (hopefully) connected to the teensy
        """
        if sys.platform.startswith('win'):
            log.debug("Using windows system.")
            ports = ['COM' + str(i + 1) for i in range(256)]

        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this is to exclude your current terminal "/dev/tty"
            log.debug("Using linux system")
            ports = glob.glob('/dev/tty[A-Za-z]*')

        elif sys.platform.startswith('darwin'):
            log.debug("Using darwin (Apple) system")
            ports = glob.glob('/dev/tty.*')

        else:
            log.error("Unsupported / uncrecognized platform")
            raise EnvironmentError('Unsupported platform')

        for port in ports:
            log.debug("Found available port: %s" % port)

        # Method 1: Match via ready-to-read serial ports
        ready_usb_devices = []
        for port in ports:
            log.info("Checking: %s" % port)
            try:
                teensy = serial.Serial(port=port, timeout=1)
                if teensy.read(4) != '':
                    log.info("Using %s" % port)
                    return teensy
            except (OSError, serial.SerialException):
                pass

    def get_next_movement_value(self):
        """Gets new data from the provided teensy object (via readline)
        and converts it into an integer.

        :returns:
            Integer value representing movement as determined by teensy, or None
        """
        raw_value = self.teensy.readline().rstrip()
        if raw_value == '':
            log.warning("Teensy returned empty string. Ignoring")
            return
        else:
            try:
                movement_value = int(raw_value)
                log.info("Read movement value: %d" % movement_value)
                return movement_value
            except:
                log.warning("(Ignoring) Couldn't convert following value to integer: %s" % raw_value)

    def is_ready(self):
        return self.teensy.isOpen()


class InFile(InputDevice):
    def __init__(self, filename):
        self._done = False
        try:
            self._file = open(filename, 'r')
            header = self._file.readline()

        except:
            log.error("Couldn't open input file.")
            sys.exit(1)

    def get_next_movement_value(self):
        line = self._file.readline()

        if line == '':
            self._done = True
            return None

        else:
            vals = line.split(",")
            return int(vals[-1].strip())

    @property
    def data_is_available(self):
        return not self._done

    def close(self):
        self._file.close()


class OutFile(object):
    def __init__(self):
        self.index = -1
        logfile_name = 'logs/%s.slp.csv' % datetime.datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
        log.info("Logging to %s" % logfile_name)
        try:
            self.logfile = open(logfile_name, 'a')
            self.logwriter = csv.writer(self.logfile)
        except Exception as e:
            log.error("Unable to open logfile: %s" % e)
            sys.exit(1)
        # Write CSV header information
        self.logwriter.writerow(['Date', 'Time', 'Reading Index', 'Movement Value'])

    def record_value(self, value):
        timestamp = datetime.datetime.now()
        date, time = str(timestamp).split(' ')
        self.logwriter.writerow([self.index, date, time, value])
        self.index += 1

    def close(self):
        self.logfile.close()
