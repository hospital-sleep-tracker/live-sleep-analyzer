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
from pysleep.utils import SleepFile, log, check_correct_run_dir
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
                        help='target sleepfile to perform analysis on',
                        nargs='+')
    args = parser.parse_args()

    # Check user is in the right directory
    check_correct_run_dir()

    for file in args.file:
        log.info("Processing %s..." % file)
        sleep_file = SleepFile(file)
        graph_with_analyzer = GraphWithAnalyzer(min_movement_value=args.minimum_value,
                                                min_movement_sum=args.minimum_sum,
                                                session_id=file)

        for sleep_entry in sleep_file.sleep_entries():
            graph_with_analyzer.add_entry(sleep_entry)

            # This call will flush the stdout, so if you are experimenting with
            # outputting data to stdout during processing, comment this out as it may interfere
            sleep_file.show_progress()
        graph_with_analyzer.show()

    # Run post-load analysis
    log.info("Processing complete. Showing results.")
    # graph_with_analyzer.show()

    # raw_input('Press `...')


if __name__ == "__main__":
    main()
