import os
import sys
import pickle
from typing import List, Tuple, Dict

try:
    from position import Position
    from solver import Solver
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

def position_to_tuple_board(pos: Position) -> Tuple[Tuple[int, ...], ...]:
    board_list: List[List[int]] = [[0] * Position.WIDTH for _ in range(Position.HEIGHT)]

    for c in range(Position.WIDTH):
        for r_internal in range(Position.HEIGHT):
            bit_index = r_internal + c * (Position.HEIGHT + 1)
            cell_mask = 1 << bit_index

            player_num = 0
            if (pos.mask & cell_mask):
                if (pos.current_position & cell_mask):
                    player_num = (pos.moves % 2) + 1
                else:
                    player_num = ((pos.moves + 1) % 2) + 1

            r_api = Position.HEIGHT - 1 - r_internal
            board_list[r_api][c] = player_num

    return tuple(tuple(row) for row in board_list)

def get_move_mask_for_col(pos: Position, col: int) -> int:
    if not (0 <= col < Position.WIDTH) or not pos.can_play(col):
        return 0
    return (pos.mask + Position.bottom_mask_col(col)) & Position.column_mask(col)

def generate_opening_book(solver: Solver, max_moves: int) -> Dict[Tuple[Tuple[int, ...], ...], int]:
    book: Dict[Tuple[Tuple[int, ...], ...], int] = {}
    initial_pos = Position()

    def recursive_gen(current_pos: Position):
        if current_pos.can_win_next():
            return
        if current_pos.nb_moves() >= Position.WIDTH * Position.HEIGHT:
            return
        if current_pos.nb_moves() >= max_moves:
            return

        board_key = position_to_tuple_board(current_pos)

        if board_key in book:
            return

        scores = solver.analyze(current_pos, weak=False)

        valid_moves_scores = [(col, score) for col, score in enumerate(scores) if score != Solver.INVALID_MOVE]

        if not valid_moves_scores:
            print(f"Warning: No valid moves found for state with {current_pos.nb_moves()} moves. Skipping.", file=sys.stderr)
            return

        best_score_current_player = -float('inf')
        if valid_moves_scores:
            best_score_current_player = max(s for col, s in valid_moves_scores)

        current_player_best_moves_cols = [col for col, s in valid_moves_scores if s == best_score_current_player]

        current_player_num = ((current_pos.nb_moves() + 1) % 2) + 1

        if current_player_num == 1:
            if not current_player_best_moves_cols:
                print(f"Error: Player 1 has no best moves for state with {current_pos.nb_moves()} moves?", file=sys.stderr)
                return

            our_chosen_move_col = current_player_best_moves_cols[0]

            book[board_key] = our_chosen_move_col

            move_mask_to_simulate = get_move_mask_for_col(current_pos, our_chosen_move_col)
            if move_mask_to_simulate == 0:
                print(f"Error getting move mask for P1 chosen col {our_chosen_move_col} at state moves={current_pos.nb_moves()}. Skipping branch.", file=sys.stderr)
                return

            pos_after_our_move = current_pos.copy()
            pos_after_our_move.play(move_mask_to_simulate)

            recursive_gen(pos_after_our_move)

        else:
            if not current_player_best_moves_cols:
                return

            for opp_move_col in current_player_best_moves_cols:
                move_mask_to_simulate = get_move_mask_for_col(current_pos, opp_move_col)
                if move_mask_to_simulate != 0:
                    pos_after_opp_move = current_pos.copy()
                    pos_after_opp_move.play(move_mask_to_simulate)
                    recursive_gen(pos_after_opp_move)

    print(f"Starting opening book generation up to {max_moves} moves (ply)...", file=sys.stderr)
    recursive_gen(initial_pos)
    print(f"Book generation finished. Total states captured for Player 1's turn: {len(book)}", file=sys.stderr)
    return book

if __name__ == "__main__":
    solver = None
    try:
        solver = Solver()
        print("AI Solver initialized successfully for book generation.", file=sys.stderr)
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to initialize AI Solver: {e}", file=sys.stderr)
        sys.exit(1)

    if solver:
        MAX_BOOK_DEPTH = 10

        generated_book = generate_opening_book(solver, MAX_BOOK_DEPTH)

        book_output_filename = f"opening_book_optimal_p2_{Position.WIDTH}x{Position.HEIGHT}_depth{MAX_BOOK_DEPTH}.pkl"

        try:
            with open(book_output_filename, 'wb') as f:
                pickle.dump(generated_book, f)
            print(f"Opening book saved to '{book_output_filename}'", file=sys.stderr)
        except Exception as e:
            print(f"Error saving opening book to '{book_output_filename}': {e}", file=sys.stderr)
            print("Book data (first 10 entries):", list(generated_book.items())[:10], file=sys.stderr)