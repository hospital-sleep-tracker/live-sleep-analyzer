"""
Use Case: Logging sleep using only Pi<->Teensy (data collection)
  - source: serial (teensy) (future wifi support)
  - save to logfile
  x realtime graph (short-term)
  x session graph (long-term)
  x realtime analysis
  x after-the-fact analysis
"""
DEBUG_ON = True
TEENSY_VENDOR_ID = 0x16c0
TEENSY_PRODUCT_ID = 0x0483
DISPLAY_GRAPH = False

import argparse, os
import logging

from pysleep import *


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(prog='python sleep-logger.py',
                                     description='Logs movement information from accelerometer input into logfile',
                                     usage='python sleep-logger.py [-h]')
    args = parser.parse_args()

    # Check user is in the right directory
    if (os.getcwd() != os.path.dirname(os.path.realpath(__file__))):
        log.error("Please cd into the script directory before running it!")
        sys.exit(1)

    # Create logs directory.
    try:
        os.listdir('logs')
        upload_new_logfiles()
    except OSError:
        try:
            os.mkdir('logs')
        except OSError:
            log.error("Can't create logs directory")
            sys.exit(1)
    logfile = None

    while True:
        sleep_reader = None
        logfile = None
        indicator_led = LightSwitch()
        try:
            # Blocking call - won't continue until a Teensy connection has been initiated
            sleep_reader = Teensy()
            logfile = OutFile()
            indicator_led.turn_on()

            while sleep_reader.is_ready():
                # Read value from accelerometer
                movement_value = sleep_reader.get_next_movement_value()

                # Handle case where bad value is received from reader
                if movement_value is None:
                    # Move on. Note: Index will still be incremented
                    indicator_led.turn_off()
                    continue
                else:
                    indicator_led.turn_on()

                logfile.record_value(movement_value)

        except KeyboardInterrupt:
            log.info("Interrupt detected. Closing logfile and quitting")
            if logfile:
                logfile.close()
            indicator_led.turn_off()
            sys.exit(0)
        except serial.SerialException:
            log.info("USB Error. Closing everything")
            indicator_led.turn_off()
            logfile.close()
        except Exception as e:
            log.error("Encountered unexpected exception: %s" % e)
            sys.exit(1)


if __name__ == "__main__":
    main()
