DEBUG_ON = True
TEENSY_VENDOR_ID = 0x16c0
TEENSY_PRODUCT_ID = 0x0483
DISPLAY_GRAPH = False

import re, time, sys, glob, os, csv, datetime, argparse
import logging as log

import serial, usb

log.basicConfig(level=log.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')

def main():
    graph = None

    # Parse command line arguments
    parser = argparse.ArgumentParser(prog='Hospital Sleep Tracker',
                                     description='Logs and analyzes realtime accelerometer input.')
    parser.add_argument('-g', '--graph', action='store_true', help='display live data via graphing tools')
    parser.add_argument('-f', '--file', dest='filename',
                        help='specify an input csv file instead of using live data')
    args = parser.parse_args()

    # Check user is in the right directory
    if (os.getcwd() != os.path.dirname(os.path.realpath(__file__))):
        log.error("Please cd into the script directory before running it!")
        sys.exit(1)

    # This is very 'unpythonic', but loading these libraries takes forever on the pi,
    # so we do it conditionally here so they're only loaded if they're needed.
    if args.graph:
        global numpy, pyplot, animation
        import numpy
        from matplotlib import pyplot, animation
        graph = LazyGraph()

    # Create logs directory.
    try:
        os.listdir('logs')
    except OSError:
        try:
            os.mkdir('logs')
        except OSError:
            log.error("Can't create logs directory")
            sys.exit(1)

    try:
        # We must initialize
        if args.filename:
            sleep_reader = InFile(args.filename)
            indicator_led = DummyLightSwitch()
            logfile = DummyLogFile()
        else:
            sleep_reader = Teensy()
            indicator_led = LightSwitch()
            logfile = OutFile()
            indicator_led.turn_on()

        analyzer = Analyzer()

        try:
            while sleep_reader.is_ready():
                # Read value from accelerometer
                movement_value = sleep_reader.get_next_movement_value()
                if movement_value is None:
                    # Got bad value from reader. Move on. Note: Index will still be incremented
                    indicator_led.turn_off()
                    continue
                else:
                    indicator_led.turn_on()

                if graph:
                    graph.add(movement_value)
                logfile.record_value(movement_value)
                analyzer.track_new_value(movement_value)

        except KeyboardInterrupt:
            log.info("Interrupt detected. Closing logfile and quitting")
            logfile.close()
            indicator_led.turn_off()
            sys.exit(0)
        except serial.SerialException:
            log.info("USB Error. Closing everything")
            indicator_led.turn_off()
            logfile.close()
            sleep_reader.close()
        except EOFError:
            log.info("Done reading file!")
            if graph:
                graph.show()
            input("Press Enter to continue...")
    except KeyboardInterrupt:
        log.info("Interrupt detected. Quitting")
        sys.exit(0)
    except Exception as e:
        log.error("Encountered unexpected exception: %s" % e)
        sleep_reader = None

class Analyzer(object):
    def __init__(self):
        self.values = []
        self.rem_sleep = True

    def track_new_value(self, value):
        self.values.append(value)


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


class DummyLightSwitch(object):
    def turn_on(self):
        pass

    def turn_off(self):
        pass


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

    def get_next_movement_value():
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

    def is_ready():
        return self.teensy.isOpen()

class InFile(InputDevice):
    def __init__(self, filename):
        try:
            self._file = open(filename, 'r')
            header = self._file.readline()

        except:
            log.error("Couldn't open input file.")
            sys.exit(1)

    def get_next_movement_value(self):
        line = self._file.readline()
        if line == '':
            raise EOFError

        else:
            vals = line.split(",")
            return int(vals[-1].strip())


class OutFile(object):
    def __init__(self):
        self.index = -1
        logfile_name = 'logs/%s.slp.csv' % datetime.datetime.now().strftime("%m%d%Y_%H%M%S")
        log.info("Logging to %s" % logfile_name)
        try:
            self.logfile = open(logfile_name, 'a')
            self.logwriter = csv.writer(logfile)
        except:
            log.error("Unable to open logfile. Quitting")
            sys.exit(1)
        # Write CSV header information
        logwriter.writerow(['Date', 'Time', 'Reading Index', 'Movement Value'])

    def record_value(self, value):
        timestamp = datetime.datetime.now()
        date, time = str(timestamp).split(' ')
        logwriter.writerow([self.index, date, time, value])
        self.index += 1

class DummyLogFile(object):
    def record_value(self, value):
        pass

if __name__ == "__main__":
    main()
