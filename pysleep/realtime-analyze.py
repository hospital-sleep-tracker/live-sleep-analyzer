"""
Use Case: Analyzing realtime data live on PC (nurse with a screen scenario)
  - source: serial (teensy)
  - save to logfile
  - realtime graph (short-term)
  - session graph (long-term)
  - realtime analysis
  x after-the-fact analysis
"""
import argparse
import serial
import sys
from pysleep.utils import SleepEntryStore, Teensy, OutFile, \
    check_correct_run_dir, log


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(prog='python realtime-analyze.py',
                                     description='Logs and performs data and garphical analysis on realtime accelerometer input')
    args = parser.parse_args()

    # Check user is in the right directory
    check_correct_run_dir()

    sleep_reader = Teensy()
    logfile = OutFile()
    sleep_entry_store = SleepEntryStore()

    try:
        # Read a sleep entry from the teensy
        for sleep_entry in sleep_reader.sleep_entries():
            # Log it
            logfile.write_entry(sleep_entry)

            # Store it
            sleep_entry_store.add_entry(sleep_entry)

    except KeyboardInterrupt:
        log.info("Interrupt detected. Press enter to quit...")
        raw_input()
    except serial.SerialException:
        log.info("USB Error. Closing current session")
    finally:
        # sleep_entry_store.show()
        logfile.close()


if __name__ == "__main__":
    main()
