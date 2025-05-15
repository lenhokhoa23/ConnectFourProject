
import sys
import argparse
import os 
import time 


try:
    if '.' not in sys.path: 
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
        solver = Solver()
    except Exception as e:
        print(f"Error initializing Solver: {e}", file=sys.stderr)
        sys.exit(1)

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
            print(f"Line {line_num}: Invalid move sequence '{line}' (failed at move {moves_played + 1})", file=sys.stderr)
        else:
            solver.reset_node_count() # Reset count for each valid position
            start_time = time.perf_counter()

            print(line, end="")

            if analyze_mode:
                try:
                    scores = solver.analyze(p, weak_mode)
                    # Print scores separated by spaces
                    for score in scores:
                        print(f" {score}", end="")
                except Exception as e:
                    print(f"\nError during analysis on line {line_num}: {e}", file=sys.stderr)
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
            print()

    print(f"\nFinished processing {line_count} lines from stdin.", file=sys.stderr)


if __name__ == "__main__":
    run_solver()