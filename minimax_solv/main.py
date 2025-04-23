# -*- coding: utf-8 -*-
# Equivalent of main.cpp for the Connect4 Solver command-line interface

import sys
import argparse
import os # For checking book file existence
import time # To measure time if needed

# --- Import necessary classes ---
# Assumes position.py, solver.py are importable relative to this script
# or available in Python path.
try:
    # Use relative imports if main.py is part of a package structure
    # from .position import Position
    # from .solver import Solver
    # If running standalone, ensure other .py files are discoverable
    if '.' not in sys.path: # Add current dir if not already there
         script_dir = os.path.dirname(__file__)
         if script_dir:
              sys.path.insert(0, script_dir)

    from position import Position
    from solver import Solver
except ImportError as e:
     print(f"Error importing required modules: {e}", file=sys.stderr)
     print("Ensure position.py and solver.py are in the same directory or Python path.", file=sys.stderr)
     sys.exit(1)
except FileNotFoundError: # Catch if script_dir fails for some reason
     print("Error determining script directory. Ensure position.py and solver.py are accessible.", file=sys.stderr)
     sys.exit(1)

def run_solver():
    """
    Main function to read positions from stdin, solve/analyze them,
    and print results to stdout, mimicking main.cpp.
    """
    parser = argparse.ArgumentParser(
        description='Solve or analyze Connect 4 positions from stdin.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
    parser.add_argument('-w', '--weak', action='store_true',
                        help='Use weak solver (score is win/loss/draw: 1/0/-1)')
    parser.add_argument('-a', '--analyze', action='store_true',
                        help='Analyze scores of all possible moves')
    # Default book name based on Position constants
    default_book = f"{Position.WIDTH}x{Position.HEIGHT}.book"
    parser.add_argument('-b', '--book', type=str, default=default_book,
                        help=f'Specify path to opening book file (default: {default_book})')

    args = parser.parse_args() # Parses sys.argv

    weak_mode = args.weak
    analyze_mode = args.analyze
    book_filename = args.book

    # --- Initialize Solver and Load Book ---
    # Check if Solver class was imported successfully
    if 'Solver' not in globals():
         print("Solver class not found. Exiting.", file=sys.stderr)
         sys.exit(1)

    try:
        solver = Solver() # __init__ handles TT init, sets book=None
    except Exception as e:
        print(f"Error initializing Solver: {e}", file=sys.stderr)
        sys.exit(1)

    # Attempt to load the specified or default opening book
    # solver.load_book handles internal logic and error messages
    solver.load_book(book_filename)

    # --- Process Input Lines ---
    print("Connect4 Solver ready. Reading positions from stdin...", file=sys.stderr)
    line_count = 0
    total_time_us = 0

    for line_num, line in enumerate(sys.stdin, 1):
        line_count += 1
        line = line.strip()
        if not line: # Skip empty lines if any
            continue

        p = Position()
        moves_played = p.play_seq(line)

        if moves_played != len(line):
            # Error handling matches C++: print error, skip output line
            print(f"Line {line_num}: Invalid move sequence '{line}' (failed at move {moves_played + 1})", file=sys.stderr)
            # Output an empty line for invalid input? C++ description suggests this.
            # print()
        else:
            # Valid position, process it
            solver.reset_node_count() # Reset count for each valid position
            start_time = time.perf_counter()

            # Print original line first, no newline yet
            print(line, end="")

            if analyze_mode:
                try:
                    scores = solver.analyze(p, weak_mode)
                    # Print scores separated by spaces
                    for score in scores:
                        print(f" {score}", end="")
                except Exception as e:
                    print(f"\nError during analysis on line {line_num}: {e}", file=sys.stderr)
                    # Decide how to handle error - skip rest of output?
                    print(" ANALYSIS_ERROR", end="") # Indicate error in output

            else: # Normal solve mode
                 try:
                    score = solver.solve(p, weak_mode)
                    print(f" {score}", end="")
                 except Exception as e:
                    print(f"\nError during solve on line {line_num}: {e}", file=sys.stderr)
                    print(" SOLVE_ERROR", end="") # Indicate error in output


            end_time = time.perf_counter()
            time_us = (end_time - start_time) * 1_000_000
            total_time_us += time_us

            # Add node count and time as mentioned in C++ description
            # Note: C++ code itself didn't print these, but description did.
            # Add them if desired.
            # print(f" {solver.get_node_count()} {int(time_us)}", end="")

            # Finish the line with a newline
            print()

    print(f"\nFinished processing {line_count} lines from stdin.", file=sys.stderr)
    # Optional: Print total time
    # print(f"Total processing time: {total_time_us / 1_000_000:.3f} seconds", file=sys.stderr)


if __name__ == "__main__":
    run_solver()