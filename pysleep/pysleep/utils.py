"""
Shared library of classes for sleep logging, analyzing, and graphing
"""
import sys
import glob
import os
import math
import csv
import datetime
import serial
import numpy
from sklearn import linear_model
from pysleeplogging import log

LIGHT_FILE = '/sys/class/leds/led0/brightness'

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

        self.index = index
        """Integer index representing which reading this was starting from 0"""

        self.movement_value = movement_value
        """Integer > 0 representing how much movement was recorded by the accelerometer"""

        self.date = date
        """String representing the date the sleep_entry was taken, in MM-DD-YYYY format.
        Note: since most sleep tracking is done overnight (duh), the logfile will usually have 2 days
        of date strings."""

        self.time = time
        """String representing the time the sleep_entry was taken in HH-MM-SS format (24 hour clock)"""

    @staticmethod
    def copy(sleep_entry, index=None, movement_value=None, date=None, time=None):
        """
        Constructor that returns a copy of the passed in sleep_entry, but with fields replaced
        with the input arguments.

        USAGE:
        original_entry = SleepEntry(index=0, movement_value=1)
        copy_entry = SleepEntry.copy(original_entry, movement_value=1000)

        RESULTS:
        print original_entry
        > "03-06-2015,18-22-09,0,1"
        print copy_entry
        > "03-06-2015,18-22-09,0,1000"
        """
        assert type(sleep_entry) == SleepEntry, "first argument must be a SleepEntry"
        return SleepEntry(index=index or sleep_entry.index,
                          movement_value=movement_value or sleep_entry.movement_value,
                          date=date or sleep_entry.date,
                          time=time or sleep_entry.time)

    @property
    def datetime(self):
        """
        Combines the stored date and time of this sleep_entry into a datetime object.
        This is useful for time comparisons.

        USAGE:
        if sleep_entry1.datetime > sleep_entry2.datetime:
            print 'sleep_entry1 happened before sleep_entry2'
        """
        return datetime.datetime.strptime("%s_%s" % (self.date, self.time), "%m-%d-%Y_%H-%M-%S")

    @staticmethod
    def header_names():
        """
        Prints the currently supported headers for a correctly formatted CSV logfile.
        This isn't used much besides for debugging, and for ensuring that logfiles read in
        have the same csv header as this expected one.
        """
        return ['Date', 'Time', 'Index', 'Movement Value']

    def __str__(self):
        """
        Override the string method so printing a sleep_entry looks pretty click
        """
        return "%s,%s,%s,%s" % (self.date, self.time, self.index, self.movement_value)


class SleepEntryStore(object):
    """Stores all sleep-entries for a session.
    Subclasses can hook onto self.add_entry and self.show in order to display graphs and run analysis.

    Usage:
        storage = SleepEntryStore()
        sleep_entry = SleepEntry(0,0)
        storage.add_entry(sleep_entry)
    """
    def __init__(self, session_id=None, **kwargs):
        self.sleep_entries = []

        self.session_id = session_id

    def add_entry(self, sleep_entry):
        """
        Adds a sleep entry to the SleepEntryStore.
        Subclasses can look at, analyze, display, or modify (not suggested) the sleep entry,
        before or after it is added.

        Ensure that subclasses call their parents!

        :param sleep_entry: a filled SleepEntry
        """
        assert type(sleep_entry) == SleepEntry, \
            "SleepEntryStore only stores values of type SleepEntries, not: %s" % type(sleep_entry)
        self.sleep_entries.append(sleep_entry)

    def show(self):
        """
        Call this function once the input has ended (USB disconnection, EOF, etc.)
        Subclasses can look at all the existing data and perform final analysis on the sleepdata as a whole
        at this point.
        """
        pass

    @property
    def num_values_recorded(self):
        return len(self.sleep_entries)

    @property
    def next_available_index(self):
        return self.num_values_recorded

    @property
    def last_recorded_index(self):
        """Returns the index of the last recorded value"""
        return self.num_values_recorded - 1


class SleepAnalyzer(SleepEntryStore):
    """
    Subclass of SleepEntryStore which performs data analysis on each entry as it is added to the datastore,
    as well as post-session analysis.
    """

    MOVEMENT_HISTORY_SIZE = 1000
    """Number of sleepentries to use for the short-term movement analysis. """

    def __init__(self, min_movement_sum=0, min_movement_value=0, **kwargs):
        super(SleepAnalyzer, self).__init__(**kwargs)

        self.min_movement_sum = min_movement_sum
        """Movement values above this amount will be printed to stdout. Only used for analysis development currently."""

        self.min_movement_value = min_movement_value

        self.max_value = 0
        """Max value recorded this session. Not very useful, but a simple example of what the SleepAnalyzer can do"""

        self.occurrences_of = {}
        """Key-Value store where the Key is the movement_value,
        and the Value is the number of times it has occurred (Mode)"""

        self.phase = 0
        """Current sleep phase."""

        self.movement_coefficients = []

        self.big_movement_entries = []

        self.movement_sums = []

        self.deteriorating_movement_sums = [0, 0]

        self.deteriorating_movement_sum_coefficients = [0, 0]

    def add_entry(self, sleep_entry):
        """This function is run immediately after the entry has been stored in the SleepEntryStore (parent.__init__).
        Any analysis to be performed on each entry should be done here."""

        # Call parent, to add value to SleepEntryStore
        super(SleepAnalyzer, self).add_entry(sleep_entry)

        # Add to big_movement_entries
        if sleep_entry.movement_value > self.min_movement_value:
            self.big_movement_entries.append(sleep_entry)

        # Add the movement_sum
        num_entries = self.MOVEMENT_HISTORY_SIZE * -1
        movement_sum = sum([x.movement_value for x in self.sleep_entries[num_entries:]])
        self.movement_sums.append(movement_sum)


        self.deteriorating_movement_sums.append(self.deteriorating_movement_sums[-1] + sleep_entry.movement_value - 1)
        if self.deteriorating_movement_sums[-1] < 0:
            self.deteriorating_movement_sums[-1] = 0

        y_values = [[y] for y in self.deteriorating_movement_sums[-50:]]
        x_values = [[x] for x in range(0, len(y_values))]
        regr = linear_model.LinearRegression()
        regr.fit(x_values, y_values)
        self.deteriorating_movement_sum_coefficients.append(regr.coef_[0][0])

        # Compare to max
        movement_value = sleep_entry.movement_value
        if movement_value > self.max_value:
            self.max_value = movement_value

        # Adjust self.occurances_of
        if movement_value not in self.occurrences_of.keys():
            self.occurrences_of[movement_value] = 1
        else:
            self.occurrences_of[movement_value] += 1



        # x_values = [[x.index] for x in self.last_entries]
        # y_values = [[y.movement_value] for y in self.last_entries]
        # movement_values = [[y.movement_value] for y in self.last_entries]
        # regr = linear_model.LinearRegression()
        # regr.fit(x_values, y_values)
        # self.movement_coefficients.append(regr.coef_[0][0])

        # if sum([x.movement_value for x in self.last_entries]) > self.min_movement_sum:
        #     print "Analyzed: %s    History Sum: %d" % (sleep_entry, sum(self.last_entries))

    def show(self):
        """
        Prints analysis information from the session up until this point.
        """
        super(SleepAnalyzer, self).show()
        log.info("Max: %d" % self.max_value)
        most_occurrences = max(self.occurrences_of)
        log.info("Mode: %s   Occurences: %d" %
                 ([k for k in self.occurrences_of if self.occurrences_of[k] == most_occurrences], most_occurrences))
        log.info("Mean: %d" % numpy.mean([sleep_entry.movement_value for sleep_entry in self.sleep_entries]))

    @property
    def last_entries(self):
        """Last X movements. Useful for analysis that needs to look at movement over the last few readings.
        Technically you could draw this from the last X entries of self.sleep_entries, but its simpler to keep it up
        to date here."""
        return self.sleep_entries[(self.MOVEMENT_HISTORY_SIZE * -1):]

    @property
    def last_movement_sum_coefficients(self):
        return self.movement_coefficients[(self.MOVEMENT_HISTORY_SIZE * -1):]

class SleepReader(object):
    """
    Base class for input devices. Subclasses should implement the get_next_sleep_entry method, and is_ready.
    All methods should call parent to keep sleep index updated.
    """
    def __init__(self, **kwargs):
        self.next_available_index = 0

    def sleep_entries(self):
        self.next_available_index += 1
        return

    def show_progress(self):
        pass


class Teensy(SleepReader):
    def __init__(self, **kwargs):
        super(Teensy, self).__init__(**kwargs)
        self.teensy = None
        """Serial object"""

        log.info("Searching for USB device")
        while self.teensy is None:
            self.teensy = self._get_teensy_usb()

    def _get_teensy_usb(self):
        """Searches, opens, and returns a serial port object connected to the Teensy.

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            An initialized serial object (hopefully) connected to the Teensy
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
        for port in ports:
            log.debug("Checking: %s" % port)
            try:
                teensy = serial.Serial(port=port, timeout=1)
                if teensy.read(4) != '':
                    log.info("Using %s" % port)
                    return teensy
            except (OSError, serial.SerialException):
                pass

    def sleep_entries(self):
        """Gets new data from the provided teensy object (via readline)
        and converts it into an integer.

        :returns:
            Integer value representing movement as determined by teensy, or None
        """
        super(Teensy, self).sleep_entries()

        for line in self.teensy:
            raw_value = line.strip()
            assert raw_value is not '', "Teensy returned empty string"
            movement_value = int(raw_value)

            log.info("Read movement value: %d" % movement_value)
            yield SleepEntry(self.next_available_index, movement_value)


class SleepFile(SleepReader):
    """Wrapper for a python file object, providing a simple interface to read sleep data from the file.

     Usage:
        The constructor is passed in a filename. After instantiation is complete, calls to get_next_sleep_entry will
        read in a new line from the file, and construct and return a SleepEntry from the data."""

    def __init__(self, filename, **kwargs):
        """Opens the specified file, and reads the header line"""
        super(SleepFile, self).__init__(**kwargs)

        self.last_sleep_entry = None
        """Used mostly for debugging malformed csv files. Constantly updated with the last SleepEntry
        that was successfully read in."""

        try:
            self._file = open(filename, 'r')
            self.total_size = os.path.getsize(filename)
            header = self._file.readline().strip()
            self.total_read = len(header)
            log.info("CSV Headers: %s" % header)
        except Exception as e:
            log.error("Couldn't open input file: %s" % e)
            sys.exit(1)

    def sleep_entries(self):
        """Probably one of the most complicated functions in this whole program. This function yields a new SleepEntry
         every time it is iterated over. WHAT? Yeah, that's what it does. It basically makes it so that you can
         use this function as a foreach to read the data, and it will stop returning SleepEntrys when there
         are none left in the file, without having to worry about counters and such..

         Example:
            sleep_file = InFile('sample_file.log')
            for sleep_entry in sleep_file.sleep_entries:
                print sleep_entry
        """
        for line in self._file:
            self.total_read += len(line)
            if line == '':
                # End of file reached
                self._file.close()
                raise StopIteration
            else:
                values = line.strip().split(",")
                assert len(values) == len(SleepEntry.header_names()), \
                    "Malformed sleepfile: %s    Last correct line: %s" % (values, self.last_sleep_entry)

                try:
                    # Convert numbers to integers, and dates/timeis
                    date = values[1]
                    time = values[2]
                    index = int(values[0])
                    movement_value = int(values[3])

                    self.last_sleep_entry = SleepEntry(index, movement_value, date, time)

                    # Yield the results. Why yield? Well, yielding means that the next time this funciton is called,
                    # it will continue where it left off, here at the yield statement.
                    yield self.last_sleep_entry
                except ValueError:
                    log.error("Malformed sleepfile: %s    Last correct line: %s" % (values, self.last_sleep_entry))

    def show_progress(self):
        percentage = math.floor((float(self.total_read) / float(self.total_size)) * 100.0)
        sys.stdout.flush()
        sys.stdout.write("\r%d%%" % percentage)


class OutFile(object):
    def __init__(self):
        """
        Creates the logfile, and writes the header row
        """
        self.logfile_name = 'logs/%s-%s.slp.csv' % (get_date_string(), get_time_string())
        log.info("Logging to %s" % self.logfile_name)
        try:
            self.logfile = open(self.logfile_name, 'a')
            self.logwriter = csv.writer(self.logfile)
        except Exception as e:
            log.error("Unable to open logfile: %s" % e)
            sys.exit(1)
        # Write CSV header information
        self.logwriter.writerow(SleepEntry.header_names())

    def write_entry(self, sleep_entry):
        self.logfile.write(str(sleep_entry) + "\r\n")

    def close(self):
        self.logfile.close()
        log.info("Log saved to %s" % self.logfile_name)


class LightSwitch(object):
    """Static object for turning off and on the Raspberry Pi's indicator LED.

    Usage:
        LightSwitch.turn_on()
        LightSwitch.turn_off()
    """
    @staticmethod
    def turn_on():
        try:
            with open(LIGHT_FILE, 'w') as f:
                f.write('1')
        except IOError:
            log.warning("Unable to turn on indicator led")

    @staticmethod
    def turn_off():
        try:
            with open(LIGHT_FILE, 'w') as f:
                f.write('0')
        except IOError:
            log.warning("Unable to turn off indicator led")


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


def check_correct_run_dir():
    if os.getcwd()[-20:] != '/live-sleep-analyzer':
        log.error("Please cd into the project directory before running any scripts!")
        sys.exit(1)
