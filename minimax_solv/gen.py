# -*- coding: utf-8 -*-
# Equivalent of generator.cpp from Connect4 Game Solver

import sys
import math
import os
from typing import Set

# Assumes position.py, opening_book.py, transposition_table.py are importable
try:
    from .position import Position
    from .opening_book import OpeningBook
    from .transposition_table import TranspositionTable
except ImportError:
    # Fallback for running standalone
    from position import Position
    from opening_book import OpeningBook
    from transposition_table import TranspositionTable


# Global set to track visited symmetric positions during exploration
visited: Set[int] = set()

def explore(p: Position, move_str: str, depth: int):
    """
    Recursively explores unique game positions up to a specified depth
    and prints the move sequence for each unique position found within the depth.
    Uses the symmetric key (key3) to avoid exploring symmetric duplicates.
    """
    key = p.key3()
    if key in visited:
        return # Already explored this symmetric position

    visited.add(key)

    nb_moves = p.nb_moves()

    # Print position if it's within the desired depth range
    if nb_moves <= depth:
        print(move_str)

    # Stop exploring further if max depth is reached
    if nb_moves >= depth:
        return

    # Explore child nodes
    for col in range(Position.WIDTH):
        if p.can_play(col) and not p.is_winning_move(col):
            p2 = p.copy()
            p2.play_col(col)
            # Append the 1-based column index to the move string
            explore(p2, move_str + str(col + 1), depth)
            # No explicit backtracking needed for move_str as strings are immutable


def generate_opening_book():
    """
    Reads scored positions from standard input and generates an opening book file.

    Input Format (stdin):
        Each line: <move_sequence> <score>
        Example: 443 10
        Input ends with EOF or an empty line.

    Output:
        Generates a file named like "WIDTHxHEIGHT.book".
    """
    # Constants from C++ code
    BOOK_SIZE = 23  # log_size for the TranspositionTable (2^23 entries)
    DEPTH = 5      # Max depth of positions expected/stored in the book

    print(f"Generating opening book (log_size={BOOK_SIZE}, depth={DEPTH}) from stdin...", file=sys.stderr)

    # Calculate partial key bits based on formula in C++
    LOG_3 = math.log2(3) # 1.58496...
    # Max bits possibly needed for key3 up to DEPTH
    # Formula: int((DEPTH + Position::WIDTH -1) * LOG_3) + 1 - BOOK_SIZE
    # Need ceiling? C++ int() truncates. Let's try floor/int first.
    max_key3_bits_approx = (DEPTH + Position.WIDTH - 1) * LOG_3
    bits_for_partial = int(max_key3_bits_approx) + 1 - BOOK_SIZE
    # Ensure at least 1 bit
    partial_key_bits = max(1, bits_for_partial)

    print(f"Calculated partial key bits: {partial_key_bits}", file=sys.stderr)

    try:
        table = TranspositionTable(log_size=BOOK_SIZE, partial_key_bits=partial_key_bits)
    except Exception as e:
        print(f"Error initializing TranspositionTable: {e}", file=sys.stderr)
        return

    count = 0
    processed_count = 0
    for line in sys.stdin:
        count += 1
        line = line.strip()
        if not line:
            break # Stop on empty line

        parts = line.split(' ', 1)
        if len(parts) != 2:
            print(f"Invalid line format (line {count} ignored): {line}", file=sys.stderr)
            continue

        pos_str, score_str = parts

        try:
            score = int(score_str)
        except ValueError:
            print(f"Invalid score format (line {count} ignored): {line}", file=sys.stderr)
            continue

        p = Position()
        # play_seq returns the number of moves successfully played
        moves_played = p.play_seq(pos_str)

        # Validate line data
        if moves_played != len(pos_str):
            print(f"Invalid position sequence '{pos_str}' (line {count} ignored): {line}", file=sys.stderr)
            continue
        if not (Position.MIN_SCORE <= score <= Position.MAX_SCORE):
            print(f"Score out of range [{Position.MIN_SCORE}, {Position.MAX_SCORE}] (line {count} ignored): {line}", file=sys.stderr)
            continue

        # Normalize score to fit uint8_t (1 to MAX_SCORE - MIN_SCORE + 1)
        # Value 0 is reserved for "miss" in TranspositionTable get()
        normalized_score = score - Position.MIN_SCORE + 1

        if not (1 <= normalized_score <= 255):
             print(f"Normalized score {normalized_score} out of range [1, 255] (line {count} ignored): {line}", file=sys.stderr)
             continue

        # Store in table using symmetric key (key3)
        table.put(p.key3(), normalized_score)
        processed_count += 1

        if processed_count % 1000000 == 0:
            print(f"Processed {processed_count} valid lines...", file=sys.stderr)

    print(f"Finished reading stdin. Processed {processed_count} valid lines out of {count-1}.", file=sys.stderr)

    if processed_count == 0:
        print("No valid lines processed. Opening book will not be saved.", file=sys.stderr)
        return

    # Create OpeningBook instance and assign the table/metadata
    # (Python OpeningBook doesn't take Table in constructor, so assign manually)
    book = OpeningBook(width=Position.WIDTH, height=Position.HEIGHT)
    book.T = table
    book.depth = DEPTH
    book._log_size = BOOK_SIZE # Store metadata needed for saving
    book._partial_key_bytes = partial_key_bits // 8
    # Ensure partial_key_bytes is valid (e.g., 1, 2, 4, 8) if TT requires specific byte sizes
    if partial_key_bits % 8 != 0 or book._partial_key_bytes not in book._KEY_FORMAT:
         print(f"Warning: Calculated partial_key_bits ({partial_key_bits}) doesn't align with supported byte sizes (1, 2, 4, 8). Saving might fail or be incompatible.", file=sys.stderr)
         # Adjust if possible or handle error in save? For now, proceed.
         # Let's refine calculation slightly: If bits=9, need 2 bytes.
         book._partial_key_bytes = math.ceil(partial_key_bits / 8)
         if book._partial_key_bytes not in book._KEY_FORMAT:
              print(f"Error: Cannot determine valid byte size for {partial_key_bits} bits.", file=sys.stderr)
              return


    # Construct filename and save
    book_filename = f"{Position.WIDTH}x{Position.HEIGHT}.book"
    print(f"Saving opening book to {book_filename}...", file=sys.stderr)
    book.save(book_filename)


# --- Main Execution Block ---
if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Explore mode
        try:
            max_depth = int(sys.argv[1])
            if max_depth < 0:
                raise ValueError("Depth cannot be negative.")
            print(f"Exploring unique positions up to depth {max_depth}...")
            # Initial call with empty position and empty move string
            explore(Position(), "", max_depth)
            print("Exploration finished.")
        except ValueError as e:
            print(f"Error: Invalid depth argument '{sys.argv[1]}'. {e}", file=sys.stderr)
            print("Usage: python generator.py [max_depth]", file=sys.stderr)
            sys.exit(1)
    else:
        # Generate opening book mode (reads from stdin)
        generate_opening_book()