# -*- coding: utf-8 -*-
# Equivalent of MoveSorter.hpp from Connect4 Game Solver

# Using bisect to maintain sorted list efficiently, similar goal to C++ insertion sort
import bisect
import math
from typing import Optional, List, Tuple

# Conceptually depends on Position.WIDTH, but not strictly needed for import.
# Assumes Position.WIDTH is relatively small (e.g., 7).

class MoveSorter:
    """
    Helps in sorting potential moves based on their scores.

    Moves are added with a score. They can then be retrieved one by one,
    starting with the move having the highest score.

    Uses `bisect` module internally to maintain moves sorted by score (ascending).
    """

    def __init__(self):
        """Initializes an empty move sorter."""
        # List of tuples: (score, move_bitmask)
        # Kept sorted by score in ascending order.
        self.entries: List[Tuple[int, int]] = []

    def add(self, move: int, score: int):
        """
        Adds a move (represented by its bitmask) and its associated score
        to the sorter, maintaining the sorted order.
        """
        # Create the entry tuple
        entry = (score, move)
        # Insert the entry into the list while maintaining sort order by score (first element)
        # bisect_left finds insertion point for 'entry' to maintain order.
        # insort_left inserts 'entry' at that point.
        bisect.insort_left(self.entries, entry)

    def get_next(self) -> Optional[int]:
        """
        Retrieves and removes the move with the highest score from the sorter.

        Returns:
            The bitmask of the move with the highest score, or None if the
            sorter is empty.
        """
        if self.entries:
            # pop() removes and returns the *last* item from the list.
            # Since the list is sorted ascending by score, the last item
            # has the highest score.
            score, move = self.entries.pop()
            return move
        else:
            # Return None if no moves are left
            return None

    def reset(self):
        """Clears all moves from the sorter."""
        self.entries = []

    def is_empty(self) -> bool:
        """Checks if the sorter contains any moves."""
        return not self.entries

# Example Usage (Conceptual)
if __name__ == "__main__":
    sorter = MoveSorter()

    # Add moves (example bitmasks and scores)
    # Assume column masks for a 7-wide board
    # col 3 mask = 1 << 3 = 8
    # col 4 mask = 1 << 4 = 16
    # col 2 mask = 1 << 2 = 4
    # col 5 mask = 1 << 5 = 32

    sorter.add(move=8, score=10)  # Col 3, score 10
    sorter.add(move=16, score=5)  # Col 4, score 5
    sorter.add(move=4, score=12)  # Col 2, score 12
    sorter.add(move=32, score=5)  # Col 5, score 5 (same as col 4)

    print(f"Internal state after adding (sorted by score): {sorter.entries}")
    # Expected internal state: [(5, 16), (5, 32), (10, 8), (12, 4)] or [(5, 32), (5, 16), (10, 8), (12, 4)]
    # (order of equal scores depends on bisect implementation detail, but doesn't affect get_next)

    print("\nGetting moves back (highest score first):")
    move = sorter.get_next()
    while move is not None:
        # Find column index from mask for clarity
        col = -1
        if move > 0:
            col = int(math.log2(move)) # Only works if move is power of 2
        print(f"Got move mask: {move} (Score was likely highest). Column: {col}")
        move = sorter.get_next()

    print(f"\nIs sorter empty now? {sorter.is_empty()}")