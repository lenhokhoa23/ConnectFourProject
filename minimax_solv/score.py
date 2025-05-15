import sys
from position import Position
from solver import Solver  

print("Initializing Solver for scoring...", file=sys.stderr)
solver_instance = Solver()


print("Reading positions from stdin and scoring...", file=sys.stderr)
count = 0
for line in sys.stdin:
    move_seq = line.strip()
    if not move_seq: continue

    p = Position()
    if p.play_seq(move_seq) == len(move_seq):
        try:
            score = solver_instance.solve(p, weak=False)
            print(f"{move_seq} {score}")
            count += 1
            if count % 1000 == 0: # In tiến trình
                 print(f"Scored {count} positions...", file=sys.stderr)
        except Exception as e:
            print(f"Error solving sequence '{move_seq}': {e}", file=sys.stderr)
    else:
        print(f"Invalid sequence skipped: {move_seq}", file=sys.stderr)

print(f"Finished scoring {count} positions.", file=sys.stderr)