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

import argparse
import serial
import sys
from pysleep.utils import Teensy, OutFile, \
    check_correct_run_dir, log
from pysleep.graphs import GraphWithAnalyzer


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(prog='python realtime-analyze.py',
                                     description='Logs and performs data and garphical analysis on realtime accelerometer input')
    args = parser.parse_args()

    # Check user is in the right directory
    check_correct_run_dir()

    sleep_reader = Teensy()
    logfile = OutFile()
    graph_with_analyzer = GraphWithAnalyzer()

    try:
        while sleep_reader.is_ready:
            movement_value = sleep_reader.get_next_sleep_entry()
            if movement_value is None:
                # Got bad value from reader. Move on. Note: Index will still be incremented
                continue

            logfile.write_entry(movement_value)
            graph_with_analyzer.add_entry(movement_value)

    except KeyboardInterrupt:
        log.info("Interrupt detected. Closing logfile")
        logfile.close()
        graph_with_analyzer.show()
        log.info("Press enter to quit...")
        raw_input()
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



if __name__ == "__main__":
    main()
