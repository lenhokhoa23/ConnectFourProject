from dataclasses import dataclass
from dis import Positions

# Lưu ý: Ở Python kiểu int có độ chính xác tùy ý, nên không cần phải quan tâm đến uint64_t hay __int128.

class Position:
    # Kích thước board
    WIDTH = 7
    HEIGHT = 6

    # Một số hằng số liên quan đến điểm số
    MIN_SCORE = -(WIDTH * HEIGHT) // 2 + 3
    MAX_SCORE = (WIDTH * HEIGHT + 1) // 2 - 3

    def __init__(self):
        # current_position và mask đều là các bitboard, dùng kiểu int ở Python
        self.current_position = 0  # chứa các ô của người chơi hiện tại
        self.mask = 0              # chứa các ô đã được đi
        self.moves = 0             # số nước đi

    # Tính các bitmask tĩnh: bottom_mask và board_mask
    @classmethod
    def compute_bottom_mask(cls) -> int:
        # Mỗi cột có vị trí bottom là bit tại index = col * (HEIGHT+1)
        return sum(1 << (col * (cls.HEIGHT + 1)) for col in range(cls.WIDTH))

    @classmethod
    def compute_board_mask(cls) -> int:
        # board_mask là tổng các mask của từng cột
        col_mask = (1 << cls.HEIGHT) - 1
        return sum(col_mask << (col * (cls.HEIGHT + 1)) for col in range(cls.WIDTH))

    # Lưu các bitmask tĩnh (chỉ tính 1 lần)
    

    # Các hàm mask cho cột
    @classmethod
    def top_mask_col(cls, col: int) -> int:
        """Bitmask có 1 tại ô trên cùng của cột."""
        return 1 << ((cls.HEIGHT - 1) + col * (cls.HEIGHT + 1))

    @classmethod
    def bottom_mask_col(cls, col: int) -> int:
        """Bitmask có 1 tại ô dưới cùng của cột."""
        return 1 << (col * (cls.HEIGHT + 1))

    @classmethod
    def column_mask(cls, col: int) -> int:
        """Bitmask có 1 tại tất cả các ô của cột."""
        return ((1 << cls.HEIGHT) - 1) << (col * (cls.HEIGHT + 1))
    
    
    # Các chức năng giao dịch (play, kiểm tra nước đi, ...)
    def play(self, move: int) -> None:
        """Chơi một nước đi với bitmask tương ứng. Hàm này cập nhật current_position và mask."""
        # Hoán đổi trạng thái current_position trước khi đặt move
        self.current_position ^= self.mask
        self.mask |= move
        self.moves += 1

    def play_col(self, col: int) -> None:
        """Chơi nước đi tại cột cho trước. Giả sử cột đó có thể chơi được."""
        move = (self.mask + Position.bottom_mask_col(col)) & Position.column_mask(col)
        self.play(move)

    def play_sequence(self, seq: str) -> int:
        """
        Chơi một chuỗi các nước đi.
        Mỗi ký tự trong seq là số cột (1-indexed). Nếu có nước đi không hợp lệ, dừng lại và trả về số nước đi đã thực hiện.
        """
        for i, ch in enumerate(seq):
            try:
                col = int(ch) - 1  # chuyển từ 1-index sang 0-index
            except ValueError:
                return i  # ký tự không hợp lệ
            if col < 0 or col >= Position.WIDTH or (self.mask & Position.top_mask_col(col)) != 0 or self.is_winning_move(col):
                return i  # nước đi không hợp lệ
            self.play_col(col)
        return len(seq)

    def can_play(self, col: int) -> bool:
        """Kiểm tra xem cột có thể chơi được không."""
        return (self.mask & Position.top_mask_col(col)) == 0

    def is_winning_move(self, col: int) -> bool:
        """
        Kiểm tra nếu người chơi hiện tại thắng khi chơi ở cột col.
        Chỉ sử dụng cho các nước đi có thể chơi được.
        """
        return (self.winning_position() & self.possible() & Position.column_mask(col)) != 0

    def can_win_next(self) -> bool:
        """Trả về True nếu người chơi hiện tại có thể thắng ngay nước tiếp theo."""
        return (self.winning_position() & self.possible()) != 0

    def nb_moves(self) -> int:
        """Trả về số nước đi đã chơi từ đầu trò chơi."""
        return self.moves

    def key(self) -> int:
        """
        Trả về key duy nhất cho vị trí hiện tại (dựa trên current_position và mask).
        """
        return self.current_position + self.mask

    def key3(self) -> int:
        """
        Xây dựng key đối xứng dựa trên hệ cơ số 3.
        Mỗi cột chuyển thành một dãy số, rồi so sánh key được tạo theo thứ tự từ trái sang phải và ngược lại.
        Trả về key nhỏ hơn sau khi chia 3 (vì chữ số cuối luôn là 0).
        """
        key_forward = 0
        for col in range(Position.WIDTH):
            key_forward = self._partial_key3(key_forward, col)
        key_reverse = 0
        for col in reversed(range(Position.WIDTH)):
            key_reverse = self._partial_key3(key_reverse, col)
        return (key_forward if key_forward < key_reverse else key_reverse) // 3

    def _partial_key3(self, key: int, col: int) -> int:
        """
        Tính toán phần của key theo cột.
        Duyệt từ ô dưới đến trên của cột (theo bit mask của cột) và cập nhật key theo hệ cơ số 3:
          - nếu ô thuộc current_position thì cộng 1
          - nếu không thì cộng 2
        Cuối mỗi cột, nhân key thêm 3.
        """
        pos = 1 << (col * (Position.HEIGHT + 1))
        while self.mask & pos:
            key *= 3
            if self.current_position & pos:
                key += 1
            else:
                key += 2
            pos <<= 1
        key *= 3
        return key

    def move_score(self, move: int) -> int:
        """
        Trả về số winning spots mà người chơi hiện tại có sau khi chơi nước đi (bitmask) move.
        Dựa trên hàm compute_winning_position.
        """
        new_position = self.current_position | move
        win_pos = Position.compute_winning_position(new_position, self.mask)
        return Position.popcount(win_pos)

    def possible_non_losing_moves(self) -> int:
        """
        Trả về bitmask của các nước đi hợp lệ mà không dẫn đến thua ngay (cho trường hợp người đối thủ có thể thắng).
        Nếu tồn tại nhiều hơn 1 forced move của đối thủ, trả về 0 vì không có cách nào ngăn được.
        """
        assert not self.can_win_next(), "Nếu có nước thắng ngay thì không cần gọi hàm này."
        possible_mask = self.possible()
        opponent_win = self.opponent_winning_position()
        forced_moves = possible_mask & opponent_win
        if forced_moves:
            # Kiểm tra xem forced_moves có nhiều hơn một nước đi không: nếu forced_moves & (forced_moves - 1) khác 0 => nhiều hơn 1
            if forced_moves & (forced_moves - 1):
                return 0  # Đối thủ có hai nước thắng, không thể chặn được
            else:
                possible_mask = forced_moves  # ép buộc phải chơi nước duy nhất có thể
        # Tránh chơi ở vị trí ngay dưới nước thắng của đối thủ
        return possible_mask & ~(opponent_win >> 1)

    def possible(self) -> int:
        """
        Trả về bitmask của tất cả nước đi có thể cho người chơi hiện tại, kể cả những nước đi dẫn thua.
        Công thức: (mask + bottom_mask) & board_mask
        """
        return (self.mask + Position.bottom_mask) & Position.board_mask

    def winning_position(self) -> int:
        """Trả về bitmask của các vị trí mà người chơi hiện tại có thể đặt để thắng ngay."""
        return Position.compute_winning_position(self.current_position, self.mask)

    def opponent_winning_position(self) -> int:
        """Trả về bitmask của các vị trí mà đối thủ có thể đặt để thắng ngay."""
        # Đối thủ có bitboard là: current_position ^ mask
        return Position.compute_winning_position(self.current_position ^ self.mask, self.mask)

    @staticmethod
    def popcount(n: int) -> int:
        """Đếm số bit 1 có trong số nguyên n."""
        return bin(n).count('1')

    @staticmethod
    def compute_winning_position(position: int, mask: int) -> int:
        """
        Tính toán bitmask các vị trí thắng (free spots) cho người chơi có bitboard `position`
        với mask của các ô đã đi là `mask`.
        Các phép dịch bit và toán tử & sẽ được thực hiện theo logic như trong C++.
        """
        r = 0
        # Vertical
        r |= (position << 1) & (position << 2) & (position << 3)

        # Horizontal
        p = (position << (Position.HEIGHT + 1)) & (position << 2 * (Position.HEIGHT + 1))
        r |= p & (position << 3 * (Position.HEIGHT + 1))
        r |= p & (position >> (Position.HEIGHT + 1))
        p = (position >> (Position.HEIGHT + 1)) & (position >> 2 * (Position.HEIGHT + 1))
        r |= p & (position << (Position.HEIGHT + 1))
        r |= p & (position >> 3 * (Position.HEIGHT + 1))

        # Diagonal 1
        p = (position << Position.HEIGHT) & (position << 2 * Position.HEIGHT)
        r |= p & (position << 3 * Position.HEIGHT)
        r |= p & (position >> Position.HEIGHT)
        p = (position >> Position.HEIGHT) & (position >> 2 * Position.HEIGHT)
        r |= p & (position << Position.HEIGHT)
        r |= p & (position >> 3 * Position.HEIGHT)

        # Diagonal 2
        p = (position << (Position.HEIGHT + 2)) & (position << 2 * (Position.HEIGHT + 2))
        r |= p & (position << 3 * (Position.HEIGHT + 2))
        r |= p & (position >> (Position.HEIGHT + 2))
        p = (position >> (Position.HEIGHT + 2)) & (position >> 2 * (Position.HEIGHT + 2))
        r |= p & (position << (Position.HEIGHT + 2))
        r |= p & (position >> 3 * (Position.HEIGHT + 2))

        # Chỉ giữ lại các vị trí trống (không có trong mask)
        return r & (Position.board_mask ^ mask)

    def __str__(self):
        """
        Hiển thị board ở dạng trực quan (cho mục đích debug).
        Các ô từ dưới lên trên, theo cột.
        """
        board = [['.' for _ in range(Position.WIDTH)] for _ in range(Position.HEIGHT)]
        # Duyệt qua từng cột
        for col in range(Position.WIDTH):
            col_mask = Position.column_mask(col)
            # Tính vị trí (bits) của cột, bắt đầu từ bottom (hàng 0)
            for row in range(Position.HEIGHT):
                bit = 1 << (col * (Position.HEIGHT + 1) + row)
                if self.mask & bit:
                    # Kiểm tra xem bit thuộc current hay không: vì current_position được cập nhật sau mỗi nước đi
                    board[row][col] = 'X' if self.current_position & bit else 'O'
        # In mảng theo thứ tự từ hàng trên xuống dưới
        lines = []
        for row in reversed(range(Position.HEIGHT)):
            lines.append(' '.join(board[row]))
        return "\n".join(lines)
    

Position.BOTTOM_MASK = Position.compute_bottom_mask()
Position.BOARD_MASK = Position.compute_board_mask()    