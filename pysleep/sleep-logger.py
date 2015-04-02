"""
Use Case: Logging sleep using only Pi<->Teensy (data collection)
  - source: serial (teensy) (future wifi support)
  - save to logfile
  x realtime graph (short-term)
  x session graph (long-term)
  x realtime analysis
  x after-the-fact analysis
"""
import argparse
import sys
import serial
import os
from pysleep.utils import check_correct_run_dir, log, \
    LightSwitch, Teensy, OutFile


def main():
    # Parse command line arguments
    argparse.ArgumentParser(prog='python sleep-logger.py',
                            description='Logs movement information from accelerometer input into logfile',
                            usage='python sleep-logger.py [-h]')

    # Check user is in the right directory
    check_correct_run_dir()

    try:
        # If log file exists, run FTP upload
        os.listdir('logs')
        # upload_new_logfiles()
    except OSError:
        try:
            # Log directory doesn't exist. create it.
            os.mkdir('logs')
        except OSError:
            log.error("Can't create logs directory")
            sys.exit(1)

    run = True
    # This loop runs once for every log session
    while run:
        sleep_log = None
        try:
            # Blocking call - won't continue until a Teensy connection has been initiated
            sleep_reader = Teensy()
            sleep_log = OutFile()
            LightSwitch.turn_on()

            for sleep_entry in sleep_reader.sleep_entries():

                # Handle case where bad value is received from reader
                if sleep_entry is None:
                    # Move on. Note: Index will still be incremented
                    LightSwitch.turn_off()
                    continue
                else:
                    LightSwitch.turn_on()

                sleep_log.write_entry(sleep_entry)

        except KeyboardInterrupt:
            log.info("Interrupt detected. Closing logfile and quitting")
            if sleep_log:
                sleep_log.close()
            LightSwitch.turn_off()
            run = False
        except serial.SerialException:
            log.info("USB Error. Closing everything")
            LightSwitch.turn_off()
            sleep_log.close()


if __name__ == "__main__":
    main()
