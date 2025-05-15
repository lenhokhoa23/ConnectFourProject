# generator.py
import sys
import math
import struct
from typing import Any, List

from Position import Position
from OpeningBook import OpeningBook
from TranspositionTable import TranspositionTable   # Phiên bản TranspositionTable đã được sửa để nhận key_size, value_size


# Global set lưu các key đã duyệt (sử dụng key3 của Position)
visited = set()

def explore(P: Position, pos_str: List[str], depth: int) -> None:
    """
    Duyệt đệ quy các nước đi hợp lệ đến độ sâu 'depth'.
    pos_str là danh sách các ký tự biểu diễn các nước đi đã thực hiện.
    """
    key = P.key3()
    if key in visited:
        return
    visited.add(key)

    nb_moves = P.nb_moves()
    # Nếu số nước đi nhỏ hơn hoặc bằng depth, in chuỗi các nước đi đã thực hiện
    if nb_moves <= depth:
        print("".join(pos_str[:nb_moves]))
    if nb_moves >= depth:
        return

    for i in range(Position.WIDTH):
        if P.can_play(i) and not P.is_winning_move(i):
            P2 = P.clone()   # Giả sử Position có method clone() trả về bản sao (deep copy).
            P2.play_col(i)
            # Gán ký tự cho nước đi tại vị trí nb_moves; ký tự '1', '2', ...
            pos_str[nb_moves] = chr(ord('1') + i)
            explore(P2, pos_str, depth)
            pos_str[nb_moves] = ''  # Reset sau khi duyệt

def generate_opening_book() -> None:
    """
    Đọc dữ liệu từ stdin để xây dựng bảng khai cuộc (opening book).
    Mỗi dòng input theo định dạng: "<move_sequence> <score>"
    Sau đó, lưu dữ liệu vào file "<WIDTH>x<HEIGHT>.book".
    """
    BOOK_SIZE = 23
    DEPTH = 14
    LOG_3 = 1.58496250072  # log_3(2) ~ 1.58496, dùng trực tiếp theo C++ code

    # Tính số bit sử dụng cho partial key theo công thức của C++
    partial_key_bits = int((DEPTH + Position.WIDTH - 1) * LOG_3) + 1 - BOOK_SIZE
    # Chuyển sang số byte (làm tròn lên)
    partial_key_bytes = max(1, (partial_key_bits + 7) // 8)
    # Sử dụng BOOK_SIZE làm log_size cho bảng chuyển vị
    table = TranspositionTable(log_size=BOOK_SIZE, key_size=partial_key_bytes, value_size=1)

    count = 1
    for line in sys.stdin:
        line = line.strip()
        if len(line) == 0:
            break
        # Tách chuỗi: phần nước đi và điểm số
        parts = line.split()
        if len(parts) < 2:
            sys.stderr.write(f"Invalid line (line ignored): {line}\n")
            continue
        pos_seq, score_str = parts[0], parts[1]
        try:
            score = int(score_str)
        except ValueError:
            sys.stderr.write(f"Invalid score (line ignored): {line}\n")
            continue

        P = Position()
        moves_played = P.play_seq(pos_seq)
        # Kiểm tra nếu nước đi không khớp hoặc score không hợp lệ
        if moves_played != len(pos_seq) or score < Position.MIN_SCORE or score > Position.MAX_SCORE:
            sys.stderr.write(f"Invalid line (line ignored): {line}\n")
            continue

        # Lưu (key3, score đã điều chỉnh) vào bảng chuyển vị.
        table.put(P.key3(), score - Position.MIN_SCORE + 1)
        if count % 1000000 == 0:
            sys.stderr.write(f"{count}\n")
        count += 1

    # Tạo opening book với bảng chuyển vị vừa xây dựng
    book = OpeningBook(Position.WIDTH, Position.HEIGHT, DEPTH, table)
    output_filename = f"{Position.WIDTH}x{Position.HEIGHT}.book"
    book.save(output_filename)
    sys.stderr.write(f"Opening book saved to {output_filename}\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            depth = int(sys.argv[1])
            pos_str = [''] * (depth + 1)
            explore(Position(), pos_str, depth)
        except ValueError:
            sys.stderr.write("Invalid depth argument.\n")
    else:
        generate_opening_book()
