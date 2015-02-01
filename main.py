DEBUG_ON = True
TEENSY_VENDOR_ID = 0x16c0
TEENSY_PRODUCT_ID = 0x0483
DISPLAY_GRAPH = False

import re, time, sys, glob
import logging as log
import pdb

import serial, usb, numpy
from matplotlib import pyplot, animation

log.basicConfig(level=log.DEBUG, format='%(asctime)s [%(levelname)s]: %(message)s')

def main():
    # Parse command line arguments
    sys.argv.pop(0)
    for arg in sys.argv:
        if arg == '--display':
            global DISPLAY_GRAPH
            DISPLAY_GRAPH = True

    if DISPLAY_GRAPH:
        display_init()

    # Main loop
    teensy = None
    while True:
        try:
            # Initialize USB reader
            while teensy == None:
                teensy = get_teensy_usb()

            # Prepare log output
            # timestamp = 'currenttime'
            # file_open(timestamp)

            buffer = [100, 120, 140]
            # Read the data
            if teensy.isOpen():
                fig = pyplot.figure()
                ax = pyplot.axes(xlim=(0, 100), ylim=(0, 200))
                line, = ax.plot([], [], lw=2)
                i = 1
                buffer = [100,120,140];
                # set up animate function
                def animate(i):
                    output=str(teensy.read(4))
                    outputre=re.split("\W+",output)
                    buffer.append(outputre[1])
                    x = numpy.linspace(0,100,len(buffer))
                   # y = int(outputre[1])
                    y = buffer
                    line.set_data(x, y)
                    #print (outputre[1])
                    #print (buffer)
                    return line,
                def init_graph():
                    line.set_data([], [])
                    return line,
                pdb.set_trace()
                anim = animation.FuncAnimation(fig, animate, init_func=init_graph,
                               frames=100, interval=20, blit=False)
                pyplot.show()


        except:
            teensy = None


def clean_graph():
    line.set_data([], [])
    return line,


def get_teensy_usb():
    """Searches, opens, and returns a serial port object connected to the teensy

    :raises EnvironmentError:
        On unsupported or unknown platforms
    :returns:
        A list of available serial ports
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

    log.debug("Available ports: %s" % ports)

    ready_usb_devices = []

    # Method 1: Match via vendor USB info
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
    #         pdb.set_trace()
    #         serial_device.close()
    #         ready_usb_devices.append(serial_device)
    #     except (OSError, serial.SerialException):
    #         log.debug("Port %s unavailable")
    #         pass

    # Method 2: Match via ready-to-read serial ports
    for port in ports:
        try:
            teensy = serial.Serial(port=port, timeout=1)
            if teensy.read(4) != '':
                return teensy
        except (OSError, serial.SerialException):
            pass


def read_from_usb(dev):
    outputre = re.split("\W+",output)
    print(output)
    print (outputre[1])
    time.sleep(1)

main()
