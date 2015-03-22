"""
Use Case: Analyzing data from logfile (after-the-fact analysis)
  - source: logfile
  x save to logfile
  x realtime graph (short-term)
  - session graph (long-term)
  x realtime analysis
  - after-the-fact analysis
"""
import argparse
import sys

from pysleep.utils import InFile, log, check_correct_run_dir
from pysleep.graphs import GraphWithAnalyzer


def main():
    # Parse command line arguments
    description = 'Imports a sleep file and performs after-the-fact data and graphical analysis on it'
    parser = argparse.ArgumentParser(prog='python post-analyze.py',
                                     description=description)
    parser.add_argument('-m', '--minimum-value',
                        type=int,
                        help='if provided, will print every entry where movement_value > x to stdout')

    parser.add_argument('-s', '--minimum-sum',
                        type=int,
                        help='if provided, will print every entry where sum of last n entires > x to stdout')

    parser.add_argument('file',
                        help='target sleepfile to perform analysis on')

    args = parser.parse_args()

    # Check user is in the right directory
    check_correct_run_dir()

    graph_with_analyzer = GraphWithAnalyzer(min_movement_value=args.minimum_value,
                                            min_movement_sum=args.minimum_sum)
    sleep_reader = InFile(args.file)

    # Main program loop
    while sleep_reader.is_ready:
        try:
            sleep_entry = sleep_reader.get_next_sleep_entry()
            if sleep_entry:
                graph_with_analyzer.add_entry(sleep_entry)
        except KeyboardInterrupt:
            log.info("Interrupt detected. Quitting")
            sleep_reader.close()
            sys.exit(0)

    # Run post-load analysis
    log.info("Loaded %d values" % graph_with_analyzer.num_values_recorded)
    sleep_reader.close()
    graph_with_analyzer.show()


if __name__ == "__main__":
    main()
