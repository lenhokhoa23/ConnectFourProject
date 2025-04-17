# ----- Thêm vào đầu file solver.py -----
import sys
import os # Để kiểm tra file book tồn tại
from typing import Optional, List # Thêm Optional nếu chưa có
try:
    # Đảm bảo import các lớp cần thiết
    from .position import Position
    from .opening_book import OpeningBook
    from .transposition_table import TranspositionTable
    from .move_sorter import MoveSorter # Đảm bảo MoveSorter được import
except ImportError:
    from position import Position
    from opening_book import OpeningBook
    from transposition_table import TranspositionTable
    from move_sorter import MoveSorter

# ----- Bên trong lớp Solver trong solver.py -----

class Solver:
    INVALID_MOVE = -1000 # Giữ nguyên hoặc điều chỉnh nếu cần

    def __init__(self):
        """Khởi tạo Solver."""
        self.node_count = 0
        self.column_order = [0] * Position.WIDTH
        for i in range(Position.WIDTH):
            self.column_order[i] = Position.WIDTH // 2 + (1 - 2 * (i % 2)) * (i + 1) // 2

        # Khởi tạo TranspositionTable (ví dụ với log_size=24, key_bits=32)
        # Bạn có thể muốn làm cho các tham số này có thể cấu hình được
        try:
             self.trans_table = TranspositionTable(log_size=24, partial_key_bits=32)
        except Exception as e:
             print(f"Critical Error: Failed to initialize TranspositionTable: {e}", file=sys.stderr)
             # Có thể thoát hoặc đặt thành None và kiểm tra sau
             self.trans_table = None # Hoặc raise exception

        # Khởi tạo OpeningBook là None ban đầu
        self.book: Optional[OpeningBook] = None

    def load_book(self, filename: str):
        """Tải opening book từ file được chỉ định."""
        # Kiểm tra file tồn tại trước để có thông báo lỗi tốt hơn
        if not os.path.exists(filename):
            print(f"Solver: Opening book file not found: {filename}", file=sys.stderr)
            self.book = None
            return

        print(f"Solver: Attempting to load book: {filename}", file=sys.stderr)
        # Truyền width/height từ hằng số của Position
        temp_book = OpeningBook(width=Position.WIDTH, height=Position.HEIGHT)
        if temp_book.load(filename):
            self.book = temp_book # Gán book nếu load thành công
            print(f"Solver: Successfully loaded book '{filename}', depth={getattr(self.book, 'depth', 'N/A')}", file=sys.stderr)
        else:
            # Load thất bại, phương thức load trong OpeningBook nên in chi tiết lỗi
            print(f"Solver: Failed to load book '{filename}'.", file=sys.stderr)
            self.book = None # Đảm bảo book là None nếu load thất bại

    def reset_node_count(self):
        """Resets the node count."""
        self.node_count = 0

    def get_node_count(self) -> int:
        """Returns the number of nodes explored."""
        return self.node_count

    # --- Cập nhật negamax để sử dụng Opening Book ---
    def negamax(self, p: Position, alpha: int, beta: int) -> int:
        """
        Hàm negamax với alpha-beta pruning và sử dụng Transposition Table / Opening Book.
        """
        # --- Kiểm tra ban đầu và điều kiện dừng ---
        assert alpha < beta
        # assert not p.can_win_next() # Giả định này được kiểm tra trước khi gọi negamax (trong solve)

        # Kiểm tra hòa (bàn đầy)
        if p.nb_moves() >= Position.WIDTH * Position.HEIGHT: # Board is full
             return 0 # Draw

        # Kiểm tra nước đi không thua còn lại
        possible = p.possible_non_losing_moves()
        if possible == 0: # Không có nước đi không thua -> thua ở lượt kế
            return -(Position.WIDTH * Position.HEIGHT - p.nb_moves()) // 2

        # Kiểm tra hòa khi chỉ còn ít ô (ví dụ: 2) và không có nước thắng tức thời
        if p.nb_moves() >= Position.WIDTH * Position.HEIGHT - 2:
            return 0

        self.node_count += 1

        # --- Cải thiện chặn Alpha-Beta dựa trên điểm số có thể ---
        min_bound = -(Position.WIDTH * Position.HEIGHT - 2 - p.nb_moves()) // 2 # Điểm thấp nhất có thể (đối phương không thắng ngay)
        if alpha < min_bound:
            alpha = min_bound
            if alpha >= beta: return alpha

        max_bound = (Position.WIDTH * Position.HEIGHT - 1 - p.nb_moves()) // 2 # Điểm cao nhất có thể (mình không thắng ngay)
        if beta > max_bound:
            beta = max_bound
            if alpha >= beta: return beta

        # --- Tra cứu Transposition Table ---
        # Sử dụng key() chuẩn cho TT (không phải key3)
        key = p.key()
        # Kiểm tra TT có được khởi tạo không
        if self.trans_table:
            tt_value = self.trans_table.get(key)
            if tt_value != 0: # Chỉ xử lý nếu có giá trị khác 0 (hit)
                # Logic giải mã giá trị TT từ C++
                if tt_value > Position.MAX_SCORE - Position.MIN_SCORE + 1:  # Lower Bound stored
                    min_bound_tt = tt_value + 2 * Position.MIN_SCORE - Position.MAX_SCORE - 2
                    if alpha < min_bound_tt:
                        alpha = min_bound_tt
                        if alpha >= beta: return alpha
                else:  # Upper Bound stored
                    max_bound_tt = tt_value + Position.MIN_SCORE - 1
                    if beta > max_bound_tt:
                        beta = max_bound_tt
                        if alpha >= beta: return beta

        # --- Tra cứu Opening Book ---
        # Sử dụng book.get(P) -> gọi P.key3() bên trong
        # Thực hiện *sau* TT lookup và *trước* tạo nước đi, như trong C++ gốc
        if self.book and self.book.is_loaded:
            book_value = self.book.get(p) # Trả về giá trị đã chuẩn hóa hoặc 0
            if book_value != 0: # Nếu tìm thấy trong book và trong độ sâu cho phép
                # Giá trị trong book đã được chuẩn hóa: score - MIN_SCORE + 1
                # Chuyển đổi lại thành điểm thực tế:
                actual_score = book_value + Position.MIN_SCORE - 1
                # Trả về ngay lập tức vì book chứa kết quả chính xác
                return actual_score

        # --- Khám phá nước đi ---
        moves = MoveSorter()
        for i in range(Position.WIDTH -1, -1, -1):
            col_index = self.column_order[i]
            move_mask = possible & Position.column_mask(col_index)
            if move_mask:
                moves.add(move_mask, p.move_score(move_mask))

        best_score = -float('inf') # Giá trị khởi tạo cho alpha

        next_move_mask = moves.get_next()
        while next_move_mask is not None: # Loop qua các nước đi đã sắp xếp
            p2 = p.copy()
            p2.play(next_move_mask)

            score = -self.negamax(p2, -beta, -alpha) # Gọi đệ quy

            if score >= beta: # Beta cut-off
                 if self.trans_table: # Lưu lower bound vào TT nếu có TT
                     tt_store_value = score + Position.MAX_SCORE - 2 * Position.MIN_SCORE + 2
                     self.trans_table.put(key, tt_store_value)
                 return score # Prune

            if score > alpha: # Tìm thấy nước đi tốt hơn
                alpha = score

            next_move_mask = moves.get_next() # Lấy nước đi tiếp theo

        # --- Lưu kết quả vào Transposition Table ---
        if self.trans_table: # Lưu upper bound (alpha) vào TT nếu có TT
             tt_store_value = alpha - Position.MIN_SCORE + 1
             self.trans_table.put(key, tt_store_value)

        return alpha # Trả về điểm tốt nhất tìm được trong khoảng [alpha, beta]

    # --- Các phương thức solve, analyze giữ nguyên như trước ---
    def solve(self, p: Position, weak: bool = False) -> int:
        # ... (giữ nguyên) ...
        # Chỉ cần đảm bảo nó gọi self.negamax(...)
        if p.can_win_next():
             return (Position.WIDTH * Position.HEIGHT + 1 - p.nb_moves()) // 2

        min_score = -(Position.WIDTH * Position.HEIGHT - p.nb_moves()) // 2
        max_score = (Position.WIDTH * Position.HEIGHT + 1 - p.nb_moves()) // 2

        if weak:
            min_score = -1
            max_score = 1

        while min_score < max_score:
            med = min_score + (max_score - min_score) // 2
            if med <= 0 and min_score // 2 < med: med = min_score // 2
            elif med >= 0 and max_score // 2 > med: med = max_score // 2

            # reset_node_count() should be outside solve loop if counting per position
            # self.reset_node_count() # Maybe reset before the while loop? Or outside solve?

            r = self.negamax(p, med, med + 1)

            if r <= med: max_score = r
            else: min_score = r

        return min_score


    def analyze(self, p: Position, weak: bool = False) -> list[int]:
         # ... (giữ nguyên) ...
         # Chỉ cần đảm bảo nó gọi self.solve(...)
        scores = [Solver.INVALID_MOVE] * Position.WIDTH
        for col in range(Position.WIDTH):
            if p.can_play(col):
                if p.is_winning_move(col):
                    scores[col] = (Position.WIDTH * Position.HEIGHT + 1 - p.nb_moves()) // 2
                else:
                    p2 = p.copy()
                    p2.play_col(col)
                    # reset_node_count() could be called before each solve if desired
                    # self.reset_node_count()
                    scores[col] = -self.solve(p2, weak)
        return scores

# ----- Kết thúc cập nhật solver.py -----