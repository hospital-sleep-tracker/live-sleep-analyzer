"""
Shared library of classes for sleep logging, analyzing, and graphing
"""
import re, time, sys, glob, os, csv, datetime, argparse
import serial, usb
from ftplib import FTP, error_perm as permission_error
import logging, logging.handlers

import numpy
from matplotlib import pyplot, animation
from socket import error as socket_error

CREDENTIALS_PROVIDED = True
try:
  from credentials import REMOTE_IP, USER, PASSWD, SYSLOG_UDP_PORT
except ImportError:
  CREDENTIALS_PROVIDED = False


ONE_MEGABYTE = 1000000

log = logging.getLogger('sleep-logger')
log.setLevel(logging.DEBUG)

# File logger
fh = logging.FileHandler('sleeplogger.log')
fh.setLevel(logging.INFO)

# Console Logger
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# Formatter
formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
ch.setFormatter(formatter)
fh.setFormatter(formatter)

# Add handlers
log.addHandler(ch)
log.addHandler(fh)

if CREDENTIALS_PROVIDED:
    sh = logging.handlers.SysLogHandler(address=(REMOTE_IP, SYSLOG_UDP_PORT))
    sh.setLevel(logging.WARNING)
    sh.setFormatter(formatter)
    log.addHandler(sh)
log.log(logging.CRITICAL, 'Logging initialized')

def upload_new_logfiles():
  if not CREDENTIALS_PROVIDED:
      log.warning("Credentials file not found! Can't upload results")
      return

    # Make sure we're in the right directory
  if (os.getcwd() != os.path.dirname(os.path.realpath(__file__))):
      log.error("Please cd into the script directory before running it!")
      sys.exit(1)

  # Setup FTP
  log.info("Connecting to FTP site")
  try:
    ftp = FTP(timeout=5)
    ftp.connect(REMOTE_IP)
    log.info("FTP Connected")
    ftp.login(USER, PASSWD)
    ftp.cwd('logs')

    sleep_logfiles = glob.glob('./logs/*.slp.csv')
    for sleep_logfile in sleep_logfiles:
      if os.stat(sleep_logfile).st_size > ONE_MEGABYTE:
        # Check if file is already on the server
        sleep_logfile_name = os.path.basename(sleep_logfile)
        files_on_server = []
        ftp.retrlines('LIST %s' % sleep_logfile_name, files_on_server.append)

        # If not, upload it
        if not files_on_server:
          log.info("Uploading %s" % sleep_logfile_name)
          opened_sleep_logfile = open(sleep_logfile)
          transfer_cmd = 'STOR %s' % sleep_logfile_name
          upload_result = ftp.storbinary(transfer_cmd, opened_sleep_logfile)
          if upload_result == '226 Transfer complete.':
              # Succesful upload. remove the logfile
              os.remove(sleep_logfile)
        else:
          log.info("File has already been uploaded: %s" % sleep_logfile_name)

    ftp.close()
    log.info("FTP closed")
  except socket_error:
    log.warning("FTP Connection refused")
  except permission_error:
    log.warning("FTP invalid credentials")
  except Exception as e:
    log.error("Unknown ftp error encountered: %s" % e)

class Data(object):
  def __init__(self):
    self.values = []
    self.rem_sleep = True

  def add(self, value):
    self.values.append(value)

  @property
  def num_values_recorded(self):
    return len(self.values)

  # Alias
  @property
  def next_available_index(self):
    return self.num_values_recorded

  @property
  def last_recorded_index(self):
    return self.num_values_recorded - 1

  def show(self):
    pass


class Analyzer(Data):
  def __init__(self):
    super(Analyzer, self).__init__()
    self.min_value = 99999999
    self.max_value = 0
    self.occurances_of = {}
    self.bumps = {}

  def add(self, value):
    assert value != None
    super(Analyzer, self).add(value)

    # Run analysis here
    if value < self.min_value:
      self.min_value = value

    if value > self.max_value:
      self.max_value = value

    try:
      self.occurances_of[value] += 1
    except KeyError:
      self.occurances_of[value] = 1

    # check for bumps
    if value >= 3:
      log.info("Bump Detected")

  def show(self):
    super(Analyzer, self).show()
    log.info("Max: %d" % self.max_value)
    log.info("Min: %d" % self.min_value)


class Graph(Data):
  """Graphs data as it is supplied"""
  def __init__(self):
    super(Graph, self).__init__()
    pyplot.ion()
    self.ax = pyplot.axes(xlim=(0, 50), ylim=(0, 200))
    self.line, = self.ax.plot(self.values, lw=2)

  def add(self, movement_value):
    self.values.append(movement_value)
    del self.values[0]
    self.line.set_data(range(0,50), self.values)
    pyplot.draw()

  def show(self):
    super(Graph, self).show()


class LazyGraph(Data):
  def __init__(self):
    super(LazyGraph, self).__init__()
    pyplot.ion()
    self.values = []
    self.ax = pyplot.axes(xlim=(0, 50), ylim=(0, 250))
    self.line, = self.ax.plot(self.values, lw=2)

  def show(self):
    super(LazyGraph, self).show()
    pyplot.ylim((0, max(self.values)))
    pyplot.xlim((0, len(self.values)))
    self.line.set_data(range(0,len(self.values)), self.values)
    pyplot.draw()


class LightSwitch(object):
    """
    Used to turn the raspberry pi indicator light on and off.
    """
    def __init__(self):
        self._is_on = False
        """
        True if light is currently on.
        False if light is currentliy off
        """

        self.light_file = None
        """
        Filepath to the RPi's light, or None if this is not an RPi.
        If 'None', calls to turn_on and turn_off will not do anything.
        """

        """RPi's have different filepaths to trigger the LEDs depending on the hardware revision,
        so we set the correct path here"""
        try:
            import RPi.GPIO
            if RPi.GPIO.RPI_REVISION == 3:
                self.light_file = '/sys/class/leds/led0/brightness'
                with open('/sys/class/leds/led0/trigger') as f:
                    f.write('none')
            elif RPi.GPIO.RPI_REVISION == 2:
                self.light_file = '/sys/class/leds/ACT/brightness'
                with open('/sys/class/leds/ACT/trigger') as f:
                    f.write('none')
        except ImportError:
            pass

    def turn_on(self):
        """Turns the light on, ONLY if it is currently off"""
        if self.light_file and not self._is_on:
            try:
                with open(self.light_file, 'w') as f:
                    f.write('1')
                self._is_on = True
            except IOError:
                log.warning("Unable to change indicator led")

    def turn_off(self):
        """Turns the ligh off, ONLY if it is currently on"""
        if self.light_file and self._is_on:
            try:
                with open(self.light_file, 'w') as f:
                    f.write('0')
                self._is_on = False
            except IOError:
                log.warning("Unable to change indicator led")


class InputDevice(object):
    def __init__(self, filename):
        pass

    def get_next_movement_value(self):
        raise NotImplementedError()

    def is_ready(self):
        raise NotImplementedError()


class Teensy(InputDevice):
    def __init__(self):
        self.teensy = None
        """Serial object"""

        log.info("Searching for USB device")
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
            log.debug("Checking: %s" % port)
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

class AnalyzerWithGraph(Analyzer, LazyGraph):
  pass