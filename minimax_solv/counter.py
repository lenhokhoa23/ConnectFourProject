# File: generate_book.py

import os
import sys
import pickle # To save the dictionary efficiently
from typing import List, Tuple, Dict

# Configure imports similar to app.py
try:
    # Assuming position.py and solver.py are in the same directory or searchable path
    from position import Position
    from solver import Solver
    # Note: We don't necessarily need OpeningBook or TranspositionTable here for GENERATION
    # but they might be imported by Solver.
    print("Successfully imported AI modules for book generation.", file=sys.stderr)
except ImportError as e:
    print(f"CRITICAL ERROR: Could not import AI modules: {e}", file=sys.stderr)
    print("Please ensure position.py and solver.py are in the same directory or sys.path.", file=sys.stderr)
    sys.exit(1)
except FileNotFoundError:
    print("CRITICAL ERROR: Error determining script directory.", file=sys.stderr)
    sys.exit(1)
except Exception as ex:
    print(f"CRITICAL ERROR: An unexpected error occurred during AI module import: {ex}", file=sys.stderr)
    sys.exit(1)

# --- Helper function to convert Position object to a hashable tuple representation ---
# This representation should match the format the API *receives* (top row first)
# so that you can use the generated dictionary with received API data.
def position_to_tuple_board(pos: Position) -> Tuple[Tuple[int, ...], ...]:
    """
    Converts a Position object's internal state (bottom-up bitboards)
    to a tuple of tuples representation (top-down, player numbers),
    suitable for a dict key and matching the expected API input format.
    0: Empty, 1: Player 1, 2: Player 2.
    """
    board_list: List[List[int]] = [[0] * Position.WIDTH for _ in range(Position.HEIGHT)]

    # Determine which player's stones are in current_position and mask based on total moves
    # Player 1 always starts (0 moves).
    # If pos.moves is even, it's Player 1's turn. Stones in pos.current_position belong to Player 2.
    # If pos.moves is odd, it's Player 2's turn. Stones in pos.current_position belong to Player 1.

    # Iterate through columns and rows (internal bottom-up)
    for c in range(Position.WIDTH):
        for r_internal in range(Position.HEIGHT):
            bit_index = r_internal + c * (Position.HEIGHT + 1)
            cell_mask = 1 << bit_index

            player_num = 0
            if (pos.mask & cell_mask): # If the cell is occupied
                if (pos.current_position & cell_mask):
                     # This stone belongs to the player whose turn just ended
                    player_num = (pos.moves % 2) + 1 # 0 moves -> P1 just ended (impossible), 1 move -> P1 just ended (P1), 2 moves -> P2 just ended (P2)
                else:
                    # This stone belongs to the player whose turn it currently is
                    player_num = ((pos.moves + 1) % 2) + 1 # 0 moves -> P1's turn (P1), 1 move -> P2's turn (P2)

            # Map internal row (bottom-up) to API row (top-down)
            r_api = Position.HEIGHT - 1 - r_internal
            board_list[r_api][c] = player_num

    # Convert list of lists to tuple of tuples for hashability
    return tuple(tuple(row) for row in board_list)

# --- Helper function to get the bitmask for a column drop ---
def get_move_mask_for_col(pos: Position, col: int) -> int:
    """
    Calculates the bitmask for dropping a piece in the specified column.
    Returns 0 if the column is full or invalid.
    """
    if not (0 <= col < Position.WIDTH) or not pos.can_play(col):
        return 0
    # This logic is from Position.play_col, just calculating the move mask
    return (pos.mask + Position.bottom_mask_col(col)) & Position.column_mask(col)


# --- Book Generation Function ---
def generate_opening_book(solver: Solver, max_moves: int) -> Dict[Tuple[Tuple[int, ...], ...], int]:
    """
    Generates an opening book (tuple_board -> column index) by exploring
    game states where both players make optimal moves according to the solver.
    Only stores states where it's Player 1's turn.

    solver: An initialized Solver instance.
    max_moves: Maximum number of total moves (ply) to explore the game tree up to.
    """
    book: Dict[Tuple[Tuple[int, ...], ...], int] = {}
    initial_pos = Position() # Starts with an empty board, 0 moves, Player 1's turn.

    def recursive_gen(current_pos: Position):
        """Recursive helper function."""
        # Stop conditions: game over, board full, or reached max depth
        if current_pos.can_win_next():
             # The current player can win immediately. This is a terminal state
             # from the perspective of needing to analyze the *next* move.
             # We don't need to record a move *from* this state in the book
             # because the game ends *now*.
             return
        if current_pos.nb_moves() >= Position.WIDTH * Position.HEIGHT: # Board is full
            return # Draw
        if current_pos.nb_moves() >= max_moves:
            return

        # Get the hashable board key in the desired format
        board_key = position_to_tuple_board(current_pos)

        # If this state is already in the book, we've explored this path
        # from another sequence of optimal moves.
        if board_key in book:
            return

        # --- Analyze the current position for the player whose turn it is ---
        # The scores returned are from the perspective of the player whose turn it is NOW.
        scores = solver.analyze(current_pos, weak=False) # Use non-weak analysis for optimal play

        # Get valid moves (column indices) and their scores
        valid_moves_scores = [(col, score) for col, score in enumerate(scores) if score != Solver.INVALID_MOVE]

        if not valid_moves_scores:
             # Should not happen if not a terminal state and not full, but handle defensively
            print(f"Warning: No valid moves found for state with {current_pos.nb_moves()} moves. Skipping.", file=sys.stderr)
            return

        # --- Determine the best move(s) for the CURRENT player ---
        # The current player wants to maximize their score.
        best_score_current_player = -float('inf')
        if valid_moves_scores:
            best_score_current_player = max(s for col, s in valid_moves_scores)

        current_player_best_moves_cols = [col for col, s in valid_moves_scores if s == best_score_current_player]

        # --- Process based on whose turn it is ---
        current_player_num = ((current_pos.nb_moves() + 1) % 2) + 1 # 1 if even moves (P1 turn), 2 if odd moves (P2 turn)

        if current_player_num == 1:
            # If it's Player 1's turn, add the state and ONE best move to the book.
            # We pick the first best move found for deterministic book generation.
            if not current_player_best_moves_cols:
                 print(f"Error: Player 1 has no best moves for state with {current_pos.nb_moves()} moves?", file=sys.stderr)
                 return # Should not happen given valid_moves_scores exists

            our_chosen_move_col = current_player_best_moves_cols[0] # The column index

            # Store this state and the chosen move in the book
            book[board_key] = our_chosen_move_col
            # print(f"Added P1 state (moves={current_pos.nb_moves()}): {board_key} -> {our_chosen_move_col}", file=sys.stderr)

            # Simulate OUR chosen move to get to the OPPONENT's (Player 2's) turn
            move_mask_to_simulate = get_move_mask_for_col(current_pos, our_chosen_move_col)
            if move_mask_to_simulate == 0:
                 print(f"Error getting move mask for P1 chosen col {our_chosen_move_col} at state moves={current_pos.nb_moves()}. Skipping branch.", file=sys.stderr)
                 return # Should not happen if can_play was true

            pos_after_our_move = current_pos.copy() # Play modifies in place, so use a copy
            pos_after_our_move.play(move_mask_to_simulate)

            # Recursively call for the state after Player 1's move (now Player 2's turn)
            recursive_gen(pos_after_our_move)

        else: # current_player_num == 2
            # If it's Player 2's turn, we DO NOT add to the book.
            # We only find Player 2's best responses and recursively explore EACH of them.
            # This ensures we explore all lines where the opponent plays optimally.

            if not current_player_best_moves_cols:
                 # Player 2 has no valid moves, game likely ended on Player 1's last turn (draw or P1 win).
                 return

            # Recursively explore the game state after EACH optimal opponent move
            for opp_move_col in current_player_best_moves_cols:
                move_mask_to_simulate = get_move_mask_for_col(current_pos, opp_move_col)
                 # Need to check move_mask_to_simulate != 0 defensively, though analyze should only return valid cols
                if move_mask_to_simulate != 0:
                    pos_after_opp_move = current_pos.copy() # Use a copy
                    pos_after_opp_move.play(move_mask_to_simulate)
                    recursive_gen(pos_after_opp_move)
                # else:
                    # print(f"Warning: Error getting move mask for P2 optimal col {opp_move_col} at state moves={current_pos.nb_moves()}. Skipping.", file=sys.stderr)


    print(f"Starting opening book generation up to {max_moves} moves (ply)...", file=sys.stderr)
    recursive_gen(initial_pos) # Start the recursion from the empty board
    print(f"Book generation finished. Total states captured for Player 1's turn: {len(book)}", file=sys.stderr)
    return book

# --- Main execution block ---
if __name__ == "__main__":
    # Initialize Solver
    solver = None
    try:
        solver = Solver()
        # We don't need to load a book here, we are creating one.
        print("AI Solver initialized successfully for book generation.", file=sys.stderr)
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to initialize AI Solver: {e}", file=sys.stderr)
        sys.exit(1) # Cannot generate book without solver

    if solver:
        # Define how many moves (ply) deep you want to generate the book
        # Be cautious: the number of states can still grow rapidly,
        # although limited by exploring only optimal lines.
        # Start with a small number, e.g., 8 or 10 moves total.
        # A 7x6 board has 42 total cells.
        # MAX_BOOK_DEPTH = 8 # Explore states with up to 8 stones (4 moves per player)
        MAX_BOOK_DEPTH = 10 # Explore states with up to 10 stones (5 moves per player)
        # MAX_BOOK_DEPTH = 12 # Explore states with up to 12 stones (6 moves per player)
        # Adjust this value based on desired book size, computation time, and memory.

        generated_book = generate_opening_book(solver, MAX_BOOK_DEPTH)

        # Define the filename to save the book
        # Use '.pkl' extension for pickle files
        book_output_filename = f"opening_book_optimal_p2_{Position.WIDTH}x{Position.HEIGHT}_depth{MAX_BOOK_DEPTH}.pkl"

        # Save the generated book to a file using pickle
        try:
            with open(book_output_filename, 'wb') as f:
                pickle.dump(generated_book, f)
            print(f"Opening book saved to '{book_output_filename}'", file=sys.stderr)
        except Exception as e:
            print(f"Error saving opening book to '{book_output_filename}': {e}", file=sys.stderr)
            print("Book data (first 10 entries):", list(generated_book.items())[:10], file=sys.stderr)