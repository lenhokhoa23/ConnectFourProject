import sys
import time
from Position import Position
from Solver import Solver  # module solver.py đã chuyển đổi
# Giả sử OpeningBook đã được tích hợp trong Solver hoặc có thể import riêng nếu cần

def main():
    weak = False
    analyze = False
    opening_book = "7x6.book"

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith('-'):
            if arg[1] == 'w':
                weak = True
            elif arg[1] == 'b':
                i += 1
                if i < len(args):
                    opening_book = args[i]
            elif arg[1] == 'a':
                analyze = True
        i += 1

    solver = Solver()
    solver.loadBook(opening_book)

    line_number = 1
    for line in sys.stdin:
        line = line.rstrip("\n")
        P = Position()
        # Giả sử hàm play() của Position trả về số nước đi đã thực hiện
        if P.play(line) != len(line):
            sys.stderr.write(f"Line {line_number}: Invalid move {P.nb_moves() + 1} \"{line}\"\n")
            # In dòng trống ra stdout nếu vị trí không hợp lệ
            print()
        else:
            start_time = time.time()
            if analyze:
                # Trả về danh sách điểm cho từng cột
                scores = solver.analyze(P, weak)
                output = line + "".join(f" {score}" for score in scores)
            else:
                score = solver.solve(P, weak)
                output = f"{line} {score}"
            # Tính thời gian (microsecond)
            elapsed = int((time.time() - start_time) * 1e6)
            # In ra: chuỗi nước đi, nodeCount và microsecond
            print(f"{output} {solver.nodeCount} {elapsed}")
        line_number += 1

if __name__ == "__main__":
    main()
