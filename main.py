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
        graph = Graph()

    # Create logs directory.
    try:
        os.listdir('logs')
    except OSError:
        try:
            os.mkdir('logs')
        except OSError:
            log.error("Can't create logs directory")
            sys.exit(1)

    while True:
        try:
            # Keep Searching / initializing USB reader until we find it
            teensy = None
            while teensy == None:
                teensy = get_teensy_usb()

            # Open logfile for this session
            try:
                logfile_name = 'logs/%s.slp.csv' % datetime.datetime.now().strftime("%m%d%Y_%H%M%S")
                log.info("Logging to %s" % logfile_name)
                logfile = open(logfile_name, 'a')
                logwriter = csv.writer(logfile)
                turn_on_led()


                # Write CSV header information
                logwriter.writerow(['Date', 'Time', 'Reading Index', 'Movement Value'])
            except:
                log.error("Unable to open logfile. Quitting")
                sys.exit(1)

            try:
                index = -1
                while teensy.isOpen():
                    index += 1
                    # Read value from accelerometer
                    movement_value = get_movement_value(teensy)
                    if movement_value is None:
                        # Got bad value from reader. Move on. Note: Index will still be incremented
                        turn_off_led()
                        continue

                    # Get a timestamp of this reading
                    turn_on_led()
                    timestamp = datetime.datetime.now()
                    date, time = str(timestamp).split(' ')

                    if graph:
                        graph.add(movement_value)
                    if logfile:
                        logwriter.writerow([index, date, time, movement_value])
            except KeyboardInterrupt:
                log.info("Interrupt detected. Closing logfile and quitting")
                logfile.close()
                turn_off_led()
                sys.exit(0)
            except serial.SerialException:
                log.info("USB Error. Closing everything")
                turn_off_led()
                logfile.close()
                teensy.close()
        except KeyboardInterrupt:
            log.info("Interrupt detected. Quitting")
            sys.exit(0)
        except Exception as e:
            log.error("Encountered unexpected exception: %s" % e)
            teensy = None

def turn_on_led():
    try:
        with open('/sys/class/leds/ACT/brightness', 'w') as f:
            f.write('1')
    except IOError:
        log.warning("Unable to change indicator led")

def turn_off_led():
    try:
        with open('/sys/class/leds/ACT/brightness', 'w') as f:
            f.write('0')
    except IOError:
        log.warning("Unable to change indicator led")

class Graph(object):
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

def get_movement_value(teensy):
    """Gets new data from the provided teensy object (via readline)
    and converts it into an integer.

    :returns:
        Integer value representing movement as determined by teensy, or None
    """
    raw_value = teensy.readline().rstrip()
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

def get_teensy_usb():
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

    # Method 2: Match via vendor USB info
    # device = None
    # while dev == None:
    #     time.sleep(1)
    #     device = usb.core.find(idVendor=TEENSY_VENDOR_ID, idProduct=TEENSY_PRODUCT_ID)

    # if device.is_kernel_driver_active(0):
    #     try:
    #         device.detach_kernel_driver(0)
    #     except usb.core.USBError as e:
    #         log.error("Could not detach kernel driver %s" % str(e))
    #         device = None

    # try:
    #     device.set_configuration()
    #     device.reset()
    # except usb.core.USBError as e:
    #     sys.exit("Could not set configuration: %s" % str(e))

    # for port in ports:
    #     try:
    #         log.info("Checking port %s" % port)
    #         serial_device = serial.Serial(port=port, timeout=2)
    #         test_line = serial_device.readline()
    #         if test_line == '':
    #             raise OSError
    #         serial_device.close()
    #         ready_usb_devices.append(serial_device)
    #     except (OSError, serial.SerialException):
    #         log.debug("Port %s unavailable")
    #         pass

if __name__ == "__main__":
    main()
