# File: scorer.py
import sys
from position import Position # Đảm bảo import đúng
from solver import Solver   # Đảm bảo import đúng

print("Initializing Solver for scoring...", file=sys.stderr)
solver_instance = Solver()
# Có thể load sách cho solver này để tăng tốc tính điểm không?
# solver_instance.load_book("7x6.book") # Tùy chọn

print("Reading positions from stdin and scoring...", file=sys.stderr)
count = 0
for line in sys.stdin:
    move_seq = line.strip()
    if not move_seq: continue

    p = Position()
    # Kiểm tra xem chuỗi có hợp lệ không và tạo đúng trạng thái p
    if p.play_seq(move_seq) == len(move_seq):
        # Gọi solve để lấy điểm chính xác
        try:
            # reset node count để theo dõi riêng từng vị trí nếu muốn
            # solver_instance.reset_node_count()
            score = solver_instance.solve(p, weak=False)
            # In ra theo định dạng yêu cầu của generator
            print(f"{move_seq} {score}")
            count += 1
            if count % 1000 == 0: # In tiến trình
                 print(f"Scored {count} positions...", file=sys.stderr)
        except Exception as e:
            print(f"Error solving sequence '{move_seq}': {e}", file=sys.stderr)
    else:
        print(f"Invalid sequence skipped: {move_seq}", file=sys.stderr)

print(f"Finished scoring {count} positions.", file=sys.stderr)