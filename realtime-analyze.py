"""
Use Case: Analyzing realtime data live on PC (nurse with a screen scenario)
  - source: serial (teensy)
  - save to logfile
  - realtime graph (short-term)
  - session graph (long-term)
  - realtime analysis
  x after-the-fact analysis
"""
DEBUG_ON = True
TEENSY_VENDOR_ID = 0x16c0
TEENSY_PRODUCT_ID = 0x0483
DISPLAY_GRAPH = False

import re, time, sys, glob, os, csv, datetime, argparse
import logging as log

import serial, usb

import pysleep

import numpy
from matplotlib import pyplot, animation

log.basicConfig(level=log.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')

def main():
    graph = None

    # Parse command line arguments
    parser = argparse.ArgumentParser(prog='Hospital Sleep Tracker',
                                     description='Logs and analyzes realtime accelerometer input.')
    args = parser.parse_args()

    # Check user is in the right directory
    if (os.getcwd() != os.path.dirname(os.path.realpath(__file__))):
        log.error("Please cd into the script directory before running it!")
        sys.exit(1)

    try:
        # We must initialize
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
