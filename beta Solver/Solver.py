# solver.py
import copy
from typing import List
from Position import Position
from TranspositionTable import TranspositionTable
from OpeningBook import OpeningBook
from MoveSorter import MoveSorter

class Solver:
    INVALID_MOVE = -1000

    def __init__(self):
        # Chọn TABLE_SIZE = 24, tức bảng có kích thước gần bằng số nguyên tố >= 2^24.
        TABLE_SIZE = 24
        # Tạo bảng chuyển vị (transposition table)
        self.transTable = TranspositionTable(log_size=TABLE_SIZE)
        # Khởi tạo opening book với kích thước board từ Position
        self.book = OpeningBook(Position.WIDTH, Position.HEIGHT)
        self.nodeCount = 0
        # Tạo thứ tự duyệt cột: sử dụng heuristic – thử trung tâm trước, sau đó bên phải, bên trái, v.v.
        # Đối với WIDTH = 7, ta mong muốn có thứ tự: [3, 4, 2, 5, 1, 6, 0].
        self.columnOrder = sorted(range(Position.WIDTH),
                                  key=lambda x: (abs(x - Position.WIDTH // 2), -x))
    
    def negamax(self, P: Position, alpha: int, beta: int) -> int:
        """
        Đệ quy đánh giá thế cờ dùng variant negamax của thuật toán alpha-beta.
        - P: vị trí hiện tại (chưa có ai thắng và người chơi hiện tại không thể thắng ngay).
        - alpha và beta: khoảng cửa sổ điểm mà ta đang xét.
        
        Trả về điểm số (hoặc bound) của vị trí, theo các quy tắc sau:
          - Nếu điểm thực tế <= alpha thì trả về giá trị trong khoảng [score, alpha].
          - Nếu điểm thực tế >= beta thì trả về giá trị trong khoảng [beta, score].
          - Ngược lại thì trả về điểm thực tế.
        """
        assert alpha < beta
        assert not P.canWinNext()

        self.nodeCount += 1

        possible = P.possibleNonLosingMoves()
        if possible == 0:
            # Nếu không có nước đi nào mà không thua ngay: tức đối thủ thắng nước tiếp theo
            return -(Position.WIDTH * Position.HEIGHT - P.nb_moves()) // 2

        if P.nb_moves() >= Position.WIDTH * Position.HEIGHT - 2:
            # Kiểm tra hòa
            return 0

        # Tính giới hạn thấp của điểm
        min_score = -(Position.WIDTH * Position.HEIGHT - 2 - P.nb_moves()) // 2
        if alpha < min_score:
            alpha = min_score
            if alpha >= beta:
                return alpha
        # Tính giới hạn cao của điểm
        max_score = (Position.WIDTH * Position.HEIGHT - 1 - P.nb_moves()) // 2
        if beta > max_score:
            beta = max_score
            if alpha >= beta:
                return beta

        key = P.key()  # Lấy key duy nhất của vị trí
        val = self.transTable.get(key)
        if val:
            # Phân biệt bound dựa trên giá trị lưu trong bảng chuyển vị:
            # Nếu val > (MAX_SCORE - MIN_SCORE + 1): ta có bound dưới.
            if val > (Position.MAX_SCORE - Position.MIN_SCORE + 1):
                min_bound = val + 2 * Position.MIN_SCORE - Position.MAX_SCORE - 2
                if alpha < min_bound:
                    alpha = min_bound
                    if alpha >= beta:
                        return alpha
            else:
                max_bound = val + Position.MIN_SCORE - 1
                if beta > max_bound:
                    beta = max_bound
                    if alpha >= beta:
                        return beta

        # Kiểm tra trong opening book
        val_book = self.book.get(P)
        if val_book:
            return val_book + Position.MIN_SCORE - 1

        moves = MoveSorter()
        # Duyệt các nước đi có thể theo thứ tự ưu tiên của columnOrder
        for col in self.columnOrder:
            move = possible & Position.column_mask(col)
            if move:
                moves.add(move, P.moveScore(move))
        
        while True:
            next_move = moves.getNext()
            if next_move == 0:
                break
            P2 = copy.deepcopy(P)
            P2.play(next_move)  # Sau nước đi, lượt của đối thủ
            score = -self.negamax(P2, -beta, -alpha)
            if score >= beta:
                self.transTable.put(key, score + Position.MAX_SCORE - 2 * Position.MIN_SCORE + 2)
                return score
            if score > alpha:
                alpha = score
        self.transTable.put(key, alpha - Position.MIN_SCORE + 1)
        return alpha

    def solve(self, P: Position, weak: bool = False) -> int:
        """
        Tính điểm của vị trí P.
        Nếu P có nước thắng ngay thì trả về giá trị đó, ngược lại sử dụng negamax để tính.
        Nếu weak = True, phạm vi điểm được thu hẹp về [-1, 1].
        """
        if P.canWinNext():
            return (Position.WIDTH * Position.HEIGHT + 1 - P.nb_moves()) // 2
        min_score = -(Position.WIDTH * Position.HEIGHT - P.nb_moves()) // 2
        max_score = (Position.WIDTH * Position.HEIGHT + 1 - P.nb_moves()) // 2
        if weak:
            min_score = -1
            max_score = 1

        while min_score < max_score:
            med = min_score + (max_score - min_score) // 2
            if med <= 0 and min_score // 2 < med:
                med = min_score // 2
            elif med >= 0 and max_score // 2 > med:
                med = max_score // 2
            r = self.negamax(P, med, med + 1)
            if r <= med:
                max_score = r
            else:
                min_score = r
        return min_score

    def analyze(self, P: Position, weak: bool = False) -> List[int]:
        """
        Phân tích điểm của từng cột khả dĩ từ vị trí P.
        Trả về danh sách điểm cho mỗi cột (nếu cột không thể chơi, trả về INVALID_MOVE).
        """
        scores = [Solver.INVALID_MOVE] * Position.WIDTH
        for col in range(Position.WIDTH):
            if P.can_play(col):
                if P.isWinningMove(col):
                    scores[col] = (Position.WIDTH * Position.HEIGHT + 1 - P.nb_moves()) // 2
                else:
                    P2 = copy.deepcopy(P)
                    P2.playCol(col)
                    scores[col] = -self.solve(P2, weak)
        return scores

    def reset(self) -> None:
        """Reset lại bộ đếm node và bảng chuyển vị."""
        self.nodeCount = 0
        self.transTable.reset()

    def loadBook(self, book_file: str) -> None:
        """Tải opening book từ file."""
        self.book.load(book_file)
