import sys
import os 
from typing import Optional, List 
try:

    from .position import Position
    from .opening_book import OpeningBook
    from .transposition_table import TranspositionTable
    from .move_sorter import MoveSorter 
except ImportError:
    from position import Position
    from opening_book import OpeningBook
    from transposition_table import TranspositionTable
    from move_sorter import MoveSorter


class Solver:
    INVALID_MOVE = -1000 

    def __init__(self):
        """Khởi tạo Solver."""
        self.node_count = 0
        self.column_order = [0] * Position.WIDTH
        for i in range(Position.WIDTH):
            self.column_order[i] = Position.WIDTH // 2 + (1 - 2 * (i % 2)) * (i + 1) // 2


        try:
             self.trans_table = TranspositionTable(log_size=24, partial_key_bits=32)
        except Exception as e:
             print(f"Critical Error: Failed to initialize TranspositionTable: {e}", file=sys.stderr)
             self.trans_table = None # Hoặc raise exception

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

        min_bound = -(Position.WIDTH * Position.HEIGHT - 2 - p.nb_moves()) // 2 # Điểm thấp nhất có thể (đối phương không thắng ngay)
        if alpha < min_bound:
            alpha = min_bound
            if alpha >= beta: return alpha

        max_bound = (Position.WIDTH * Position.HEIGHT - 1 - p.nb_moves()) // 2 # Điểm cao nhất có thể (mình không thắng ngay)
        if beta > max_bound:
            beta = max_bound
            if alpha >= beta: return beta


        key = p.key()
        # Kiểm tra TT có được khởi tạo không
        if self.trans_table:
            tt_value = self.trans_table.get(key)
            if tt_value != 0: 
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

        if self.book and self.book.is_loaded:
            book_value = self.book.get(p) # Trả về giá trị đã chuẩn hóa hoặc 0
            if book_value != 0: # Nếu tìm thấy trong book và trong độ sâu cho phép

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

            if score > alpha:
                alpha = score

            next_move_mask = moves.get_next() # Lấy nước đi tiếp theo

        if self.trans_table: 
             tt_store_value = alpha - Position.MIN_SCORE + 1
             self.trans_table.put(key, tt_store_value)

        return alpha 

    def solve(self, p: Position, weak: bool = False) -> int:

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


            r = self.negamax(p, med, med + 1)

            if r <= med: max_score = r
            else: min_score = r

        return min_score


    def analyze(self, p: Position, weak: bool = False) -> list[int]:

        scores = [Solver.INVALID_MOVE] * Position.WIDTH
        for col in range(Position.WIDTH):
            if p.can_play(col):
                if p.is_winning_move(col):
                    scores[col] = (Position.WIDTH * Position.HEIGHT + 1 - p.nb_moves()) // 2
                else:
                    p2 = p.copy()
                    p2.play_col(col)
               
                    scores[col] = -self.solve(p2, weak)
        return scores

