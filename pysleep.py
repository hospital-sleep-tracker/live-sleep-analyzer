"""
Shared library of classes for sleep logging, analyzing, and graphing
"""
import time
import sys
import glob
import os
import csv
import datetime
import serial
from ftplib import FTP, error_perm as permission_error
import logging
import logging.handlers
import numpy

from matplotlib import pyplot
from socket import error as socket_error

CREDENTIALS_PROVIDED = True
try:
    from credentials import REMOTE_IP, USER, PASSWD
except ImportError:
    CREDENTIALS_PROVIDED = False

MIN_SIZE_FOR_UPLOAD = 1000000


log = logging.getLogger('sleep-logger')
log.setLevel(logging.DEBUG)

# Create File logger
fh = logging.FileHandler('sleeplogger.log')
fh.setLevel(logging.INFO)

# Create Console Logger
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# Set Formatter
formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
ch.setFormatter(formatter)
fh.setFormatter(formatter)

# Add handlers
log.addHandler(ch)
log.addHandler(fh)

def upload_new_logfiles():
    """
    Global function which quickly scans for log files which exist locally, but not on the remote fileserver.
    Any files which meet the criteria are uploaded, then removed locally.
    """
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

        sleep_logs = glob.glob('./logs/*.slp.csv')
        log.info("Found local logfiles: %s" % slee_logs)
        for sleep_log in sleep_logs:
            sleep_log_filename = os.path.basename(sleep_log)
            if os.stat(sleep_log).st_size < MIN_SIZE_FOR_UPLOAD:
                log.info("Skipping %s: sleeplog is < %s bytes " % (sleep_log_filename, MIN_SIZE_FOR_UPLOAD))
                continue

            # Check if file is already on the server
            files_on_server = []
            ftp.retrlines('LIST %s' % sleep_log_filename, files_on_server.append)
            if files_on_server:
                log.info("Skipping %s: sleeplog is already on server" % sleep_log_filename, MIN_SIZE_FOR_UPLOAD)
                continue

            # If not, upload it
            log.info("Uploading %s" % sleep_log_filename)
            opened_sleep_log = open(sleep_log)
            transfer_cmd = 'STOR %s' % sleep_log_filename
            upload_result = ftp.storbinary(transfer_cmd, opened_sleep_log)
            if upload_result == '226 Transfer complete.':
                # Successful upload. remove the logfile
                log.info("Upload successful")
                os.remove(sleep_log)
            else:
                log.warning("Upload unsuccessful")

        ftp.close()
        log.info("FTP closed")
    except socket_error:
        log.warning("FTP Connection refused")
    except permission_error:
        log.warning("FTP invalid credentials")
    except Exception as e:
        log.error("Unknown ftp error encountered: %s" % e)


class SleepEntryStore(object):
    def __init__(self):
        self.values = []

    def add_entry(self, values):
        assert type(values) == SleepEntry, \
            "SleepEntryStore only stores values of type SleepEntries, not: %s" % type(values)
        self.values.append(values)

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


class SleepAnalyzer(SleepEntryStore):
    MOVEMENT_HISTORY_SIZE = 50

    def __init__(self, min_movement_sum=0, **kwargs):
        super(SleepAnalyzer, self).__init__(**kwargs)
        self.min_movement_sum = min_movement_sum
        """
        Movement values above this amount will be printed to stdout
        """

        self.max_value = 0
        self.occurrences_of = {}
        self.bumps = {}
        self.phase = 0
        self.last_values = [0] * self.MOVEMENT_HISTORY_SIZE

    def add_entry(self, sleep_entry):
        """This function is run immediately after the entry has been stored in the SleepEntryStore (parent.__init__).
        Any analysis to be performed on each entry should be run here.

        :return: None
        """
        # call parent, to add value to SleepEntryStore
        super(SleepAnalyzer, self).add_entry(sleep_entry)

        # We only care about the movement value for analysis
        movement_value = sleep_entry.movement_value

        # Shift the new movement_value into the last_values
        self.last_values.append(movement_value)
        self.last_values.pop(0)

        # Then run analysis
        if movement_value > self.max_value:
            self.max_value = movement_value

        if movement_value not in self.occurances_of.keys():
            self.occurrences_of[movement_value] = 1
        else:
            self.occurrences_of[movement_value] = 1

        if sum(self.last_values) > self.min_movement_sum:
            print sleep_entry, sum(self.last_values)

    def show(self):
        """
        Prints analysis information drawn from the session up until this point.
        """
        super(SleepAnalyzer, self).show()
        log.info("Max: %d" % self.max_value)
        most_occurrences = max(self.occurrences_of)
        log.info("Mode: %d   Occurences: %d" %
                 ([k for k in self.occurences_of if self.occurences_of[k] == most_occurrences], most_occurrences))
        log.info("Mean: %d" % numpy.mean(self.values))


class Graph(SleepEntryStore):
    def __init__(self, **kwargs):
        super(Graph, self).__init__(**kwargs)
        pyplot.ion()
        self.ax = pyplot.axes(xlim=(0, 50), ylim=(0, 200))
        self.line, = self.ax.plot(self.values, lw=2)

    def add(self, values):
        self.values.append(values['Movement Value'])
        del self.values[0]
        self.line.set_data(range(0, 50), self.values)
        pyplot.draw()

    def show(self):
        super(Graph, self).show()


class LazyGraph(SleepEntryStore):
    def __init__(self):
        super(LazyGraph, self).__init__()
        pyplot.ion()
        self.values = []
        self.ax = pyplot.axes(xlim=(0, 50), ylim=(0, 250))
        self.line, = self.ax.plot(self.values, lw=2)

    def show(self):
        super(LazyGraph, self).show()
        pyplot.ylim((0, 100))
        pyplot.xlim((0, len(self.values)))
        self.line.set_data(range(0, len(self.values)), [value['Movement Value'] for value in self.values])
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


class SleepReader(object):
    def __init__(self, filename):
        self.next_available_index = 0

    def get_next_sleep_entry(self):
        self.next_available_index += 1

    def is_ready(self):
        raise NotImplementedError()


class Teensy(SleepReader):
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

    def get_next_sleep_entry(self):
        """Gets new data from the provided teensy object (via readline)
        and converts it into an integer.

        :returns:
            Integer value representing movement as determined by teensy, or None
        """
        super(Teensy, self).get_next_sleep_entry()

        raw_value = self.teensy.readline().strip()
        assert raw_value is not '', "Teensy returned empty string"
        movement_value = int(raw_value)

        log.info("Read movement value: %d" % movement_value)
        return SleepEntry(self.next_available_index, movement_value)


    def is_ready(self):
        return self.teensy.isOpen()


class InFile(SleepReader):
    def __init__(self, filename):
        self.last_sleep_entry = None
        try:
            self._file = open(filename, 'r')
            header = self._file.readline().strip()
            log.info("CSV Headers: %s" % header)
        except Exception as e:
            log.error("Couldn't open input file: %s" % e)
            sys.exit(1)

    def get_next_sleep_entry(self):
        line = self._file.readline()

        if line == '':
            # End of file reached
            self._done = True
        else:
            values = line.strip().split(",")
            assert len(values) == len(SleepEntry.header_names()), \
                "Malformed sleepfile! Last correct line: %s" % self.last_sleep_entry

            try:
                # Convert numbers to integers, and dates/timeis
                index = int(values[0])
                date = datetime.datetime.strptime("%s" % values[1], "%m-%d-%Y")
                time = datetime.datetime.strptime("%s" % values[2], "%H-%M-%S")
                movement_value = int(values[3])


                self.last_sleep_entry = SleepEntry(index, movement_value, date, time)
                return self.last_sleep_entry
            except ValueError:
                log.error("Malformed sleepfile! Last correct line: %s" % self.last_sleep_entry)


    @property
    def data_is_available(self):
        return not self._done

    def close(self):
        self._file.close()

def get_date_string():
    """
    :return: A string representation of the current date as mm-dd-yyyy
    """
    return datetime.datetime.now().strftime("%m-%d-%Y")

def get_time_string():
    """
    :return: A string representation of the current time as hh-mm-sss
    """
    return datetime.datetime.now().strftime("%H-%M-%S")


class SleepEntry(object):
    """
    A simple storage container for the sleep data.
    Will use current date and time if either is not provided
    """
    def __init__(self, index, movement_value, date=None, time=None):
        if date is None:
            date = get_date_string()

        if time is None:
            time = get_time_string()

        self.date = date
        self.time = time
        self.index = index
        self.movement_value = movement_value

    @property
    def datetime(self):
        return datetime.datetime.strptime("%s_%s" % (self.date, self.time), "%m-%d-%Y_%H-%M-%S")

    @staticmethod
    def header_names():
        return ['Date', 'Time', 'Index', 'Movement Value']

    def __str__(self):
        return "%s,%s,%s,%s" % (self.date, self.time, self.index, self.movement_value)


class OutFile(object):
    def __init__(self):
        """
        Creates the logfile, and writes the header row
        """
        logfile_name = 'logs/%s-%s.slp.csv' % (get_date_string(), get_time_string())
        log.info("Logging to %s" % logfile_name)
        try:
            self.logfile = open(logfile_name, 'a')
            self.logwriter = csv.writer(self.logfile)
        except Exception as e:
            log.error("Unable to open logfile: %s" % e)
            sys.exit(1)
        # Write CSV header information
        self.logwriter.writerow(SleepEntry.header_names())

        def record_value(self, value):
            self.logwriter.writerow(value)

        def close(self):
            self.logfile.close()


class AnalyzerWithGraph(SleepAnalyzer, LazyGraph):
    pass
