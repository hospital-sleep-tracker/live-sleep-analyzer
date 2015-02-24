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

import numpy
from matplotlib import pyplot, animation
from pysleep import *

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(prog='python realtime-analyze.py',
                                     description='Logs and performs data and garphical analysis on realtime accelerometer input')
    args = parser.parse_args()

    # Check user is in the right directory
    if (os.getcwd() != os.path.dirname(os.path.realpath(__file__))):
        log.error("Please cd into the script directory before running it!")
        sys.exit(1)

    try:
        sleep_reader   = Teensy()
        logfile        = OutFile()
        graph_with_analyzer = AnalyzerWithGraph()

        try:
            while sleep_reader.is_ready():
                movement_value = sleep_reader.get_next_movement_value()
                if movement_value is None:
                    # Got bad value from reader. Move on. Note: Index will still be incremented
                    continue

                logfile.record_value(movement_value)
                graph_with_analyzer.add(movement_value)
                graph_with_analyzer.show()

        except KeyboardInterrupt:
            log.info("Interrupt detected. Closing logfile and quitting")
            logfile.close()
            sys.exit(0)
        except serial.SerialException:
            log.info("USB Error. Closing everything")
            logfile.close()
            sleep_reader.close()
        except EOFError:
            log.info("Done reading file!")
            if graph_with_analyzer:
                graph_with_analyzer.show()
            input("Press Enter to continue...")
    except Exception as e:
        log.error("Encountered unexpected exception: %s" % e)
        sleep_reader = None


if __name__ == "__main__":
    main()
