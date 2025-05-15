
import sys
import math
from typing import Optional, List

class Position:

    WIDTH = 7
    HEIGHT = 6
    MIN_SCORE = -(WIDTH * HEIGHT) // 2 + 3
    MAX_SCORE = (WIDTH * HEIGHT + 1) // 2 - 3

    _bottom_mask = 0
    for col in range(WIDTH): _bottom_mask |= 1 << (col * (HEIGHT + 1))
    BOTTOM_MASK = _bottom_mask
    BOARD_MASK = BOTTOM_MASK * ((1 << HEIGHT) - 1)

    @staticmethod
    def top_mask_col(col: int) -> int: return 1 << ((Position.HEIGHT - 1) + col * (Position.HEIGHT + 1))
    @staticmethod
    def bottom_mask_col(col: int) -> int: return 1 << (col * (Position.HEIGHT + 1))
    @staticmethod
    def column_mask(col: int) -> int:
        if not (0 <= col < Position.WIDTH): return 0
        return ((1 << Position.HEIGHT) - 1) << (col * (Position.HEIGHT + 1))

    if hasattr(int, "bit_count"):
        @staticmethod
        def popcount(m: int) -> int: return m.bit_count()
    else:
        @staticmethod
        def popcount(m: int) -> int: 
            c=0; 
            while m>0: 
                m&=m-1; 
                c+=1; 
            return c

    @staticmethod
    def compute_winning_position(position: int, mask: int) -> int:
        r=(position<<1)&(position<<2)&(position<<3);h_shift=Position.HEIGHT+1;p=(position<<h_shift)&(position<<2*h_shift);r|=p&(position<<3*h_shift);r|=p&(position>>h_shift);p=(position>>h_shift)&(position>>2*h_shift);r|=p&(position<<h_shift);r|=p&(position>>3*h_shift);d1_shift=Position.HEIGHT;p=(position<<d1_shift)&(position<<2*d1_shift);r|=p&(position<<3*d1_shift);r|=p&(position>>d1_shift);p=(position>>d1_shift)&(position>>2*d1_shift);r|=p&(position<<d1_shift);r|=p&(position>>3*d1_shift);d2_shift=Position.HEIGHT+2;p=(position<<d2_shift)&(position<<2*d2_shift);r|=p&(position<<3*d2_shift);r|=p&(position>>d2_shift);p=(position>>d2_shift)&(position>>2*d2_shift);r|=p&(position<<d2_shift);r|=p&(position>>3*d2_shift);return r&(Position.BOARD_MASK^mask)

    def __init__(self):
        self.current_position: int = 0; self.mask: int = 0; self.moves: int = 0

    def copy(self):
        new_pos = Position(); new_pos.current_position = self.current_position; new_pos.mask = self.mask; new_pos.moves = self.moves; return new_pos

    def play(self, move: int):
        self.current_position ^= self.mask; self.mask |= move; self.moves += 1

    def play_col(self, col: int):
        move = (self.mask + Position.bottom_mask_col(col)) & Position.column_mask(col)
        if move != 0: self.play(move)

    def play_seq(self, seq: str) -> int:
        processed_moves = 0
        for char in seq:
            if not char.isdigit(): return processed_moves; col = int(char) - 1
            if not (0 <= col < Position.WIDTH): return processed_moves
            if not self.can_play(col): return processed_moves
            if self.is_winning_move(col): return processed_moves
            self.play_col(col); processed_moves += 1
        return processed_moves

    def can_play(self, col: int) -> bool: return (self.mask & Position.top_mask_col(col)) == 0
    def is_winning_move(self, col: int) -> bool:
        move_pos = (self.mask + Position.bottom_mask_col(col)) & Position.column_mask(col)
        return bool(self.winning_position() & move_pos)

    def winning_position(self) -> int: return self.compute_winning_position(self.current_position, self.mask)
    def opponent_winning_position(self) -> int:
        opponent_position = self.current_position ^ self.mask
        return self.compute_winning_position(opponent_position, self.mask)

    def possible(self) -> int: return (self.mask + Position.BOTTOM_MASK) & Position.BOARD_MASK
    def can_win_next(self) -> bool: return bool(self.winning_position() & self.possible())
    def possible_non_losing_moves(self) -> int:
        _possible = self.possible(); _opponent_win = self.opponent_winning_position(); _forced_moves = _possible & _opponent_win
        if _forced_moves:
            if _forced_moves & (_forced_moves - 1): return 0
            else: _possible = _forced_moves
        return _possible & ~(_opponent_win >> 1)

    def move_score(self, move: int) -> int:
        if self.winning_position() & move: return 1000
        opponent_wins = self.opponent_winning_position()
        if opponent_wins & move: return 900
        col = -1
        if move > 0:
            try: bottom_bit_index = (move & -move).bit_length() - 1;
            except AttributeError: bottom_bit_index = -1 # Fallback
            if bottom_bit_index >= 0: col = bottom_bit_index // (Position.HEIGHT + 1)
        center_score = 0
        if col != -1: center_score = (Position.WIDTH // 2) - abs(col - Position.WIDTH // 2)
        return center_score

    def nb_moves(self) -> int: return self.moves
    def key(self) -> int: return self.current_position + self.mask

    def _partial_key3(self, current_key: int, col: int) -> int:
        key = current_key; pos_mask = 1 << (col * (Position.HEIGHT + 1))
        while pos_mask & self.mask:
            key *= 3; key += (1 if pos_mask & self.current_position else 2); pos_mask <<= 1
        key *= 3; return key
    def key3(self) -> int:
        key_forward = 0; key_reverse = 0
        for i in range(Position.WIDTH): key_forward = self._partial_key3(key_forward, i)
        for i in range(Position.WIDTH -1, -1, -1): key_reverse = self._partial_key3(key_reverse, i)
        return min(key_forward, key_reverse) // 3

    def __str__(self) -> str:
        rows=[];player_char="X";opponent_char="O";opponent_position=self.current_position^self.mask
        for r in range(Position.HEIGHT-1,-1,-1):
            row_str=[];
            for c in range(Position.WIDTH):
                bit_pos=1<<(r+c*(Position.HEIGHT+1))
                if self.current_position&bit_pos:row_str.append(player_char)
                elif opponent_position&bit_pos:row_str.append(opponent_char)
                else:row_str.append(".")
            rows.append(" ".join(row_str))
        separator="\n"+"+".join(["-"]*Position.WIDTH);cols_label=" ".join(map(str,range(1,Position.WIDTH+1)))
        return "\n".join(rows)+separator+"\n"+cols_label+f"\nMoves: {self.moves}"

