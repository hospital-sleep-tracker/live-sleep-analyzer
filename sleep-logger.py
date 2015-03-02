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

from pysleep import *


def main():
    # Parse command line arguments
    argparse.ArgumentParser(prog='python sleep-logger.py',
                            description='Logs movement information from accelerometer input into logfile',
                            usage='python sleep-logger.py [-h]')

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

    run = True
    # This loop runs once for every log session
    while run:
        sleep_log = None
        try:
            # Blocking call - won't continue until a Teensy connection has been initiated
            sleep_reader = Teensy()
            sleep_log = OutFile()
            LightSwitch.turn_on()

            while sleep_reader.is_ready():
                # Read value from accelerometer
                sleep_entry = sleep_reader.get_next_sleep_entry()

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
