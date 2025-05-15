
import sys
import os
import time
import random
import argparse 
from typing import Optional, List, Tuple

try:
    if '.' not in sys.path:
         script_dir = os.path.dirname(__file__)
         if script_dir:
              sys.path.insert(0, script_dir)
    from position import Position
    from solver import Solver
except ImportError as e:
     print(f"Error importing required modules: {e}", file=sys.stderr)
     print("Ensure position.py and solver.py are in the same directory or Python path.", file=sys.stderr)
     sys.exit(1)
except FileNotFoundError:
     print("Error determining script directory. Ensure position.py and solver.py are accessible.", file=sys.stderr)
     sys.exit(1)


def display_board(p: Position):
    """Prints the current board state to the console."""
    print("\n" + "="*20)
    print(p) 
    print("="*20 + "\n")

def get_player_move(p: Position) -> int:
    """Prompts the human player for a move and validates it."""
    while True:
        try:
            col_str = input(f"Your move (column 1-{Position.WIDTH}): ")
            if not col_str: continue

            col = int(col_str)
            if 1 <= col <= Position.WIDTH:
                col_index = col - 1
                if p.can_play(col_index):
                    return col_index
                else:
                    print(f"Error: Column {col} is full. Try again.")
            else:
                print(f"Error: Please enter a column number between 1 and {Position.WIDTH}.")
        except ValueError:
            print("Error: Invalid input. Please enter a number.")
        except EOFError:
             print("\nExiting game.")
             sys.exit(0)
        except KeyboardInterrupt:
             print("\nExiting game.")
             sys.exit(0)


def get_ai_move(solver: Solver, p: Position) -> int:
    """Determines the AI's best move using the solver."""
    print("AI is thinking...")
    solver.reset_node_count()
    start_time = time.perf_counter()
    scores = solver.analyze(p, weak=False)
    end_time = time.perf_counter()
    time_ms = (end_time - start_time) * 1000

    best_score = -float('inf')
    best_moves = []

    print("AI Analysis Scores:")
    score_str = []
    valid_cols = []
    for col, score in enumerate(scores):
        if p.can_play(col):
            valid_cols.append(col)
            score_str.append(f"Col {col+1}: {score}")
            if score > best_score:
                best_score = score
                best_moves = [col]
            elif score == best_score:
                best_moves.append(col)
        else:
            score_str.append(f"Col {col+1}: N/A")

    print(" | ".join(score_str))
    print(f"Nodes explored: {solver.get_node_count()}")
    print(f"Time taken: {time_ms:.2f} ms")

    if not best_moves:
        print("AI Error: No valid moves found? Choosing a random valid move.", file=sys.stderr)
        possible_cols = [c for c in range(Position.WIDTH) if p.can_play(c)]
        if not possible_cols: return -1
        return random.choice(possible_cols)

    chosen_move = random.choice(best_moves)
    print(f"AI recommends moves: {[m+1 for m in best_moves]} (Score: {best_score})")
    return chosen_move

def check_win(p: Position) -> bool:
    """Checks if the player who *just* made a move has won."""
    last_player_mask = p.mask ^ p.current_position
    if last_player_mask == 0: return False
    # Vertical
    m = last_player_mask & (last_player_mask >> 1)
    m = m & (m >> 2)
    if m != 0: return True
    # Horizontal
    h_shift = Position.HEIGHT + 1
    m = last_player_mask & (last_player_mask >> h_shift)
    m = m & (m >> (2 * h_shift))
    if m != 0: return True
    # Diagonal \
    d1_shift = Position.HEIGHT
    m = last_player_mask & (last_player_mask >> d1_shift)
    m = m & (m >> (2 * d1_shift))
    if m != 0: return True
    # Diagonal /
    d2_shift = Position.HEIGHT + 2
    m = last_player_mask & (last_player_mask >> d2_shift)
    m = m & (m >> (2 * d2_shift))
    if m != 0: return True
    return False

def check_game_over(p: Position, last_player_num: int) -> Optional[str]:
    """Checks if the game has ended in a win or draw."""
    if check_win(p):
        return f"Player {last_player_num} Wins!"
    if p.nb_moves() == Position.WIDTH * Position.HEIGHT:
        return "It's a Draw!"
    return None


# --- Sửa đổi hàm play_game ---
def play_game(human_starts: bool = True): # Thêm tham số human_starts, mặc định là True
    """
    Chạy game Connect 4 1v1.

    Args:
        human_starts: True nếu người chơi đi trước, False nếu AI đi trước.
    """
    print("Welcome to Connect 4!")
    if human_starts:
        print("Human (Player 1) vs AI (Player 2)")
    else:
        print("AI (Player 1) vs Human (Player 2)")

    # --- Initialize ---
    try:
        p = Position()
        solver = Solver()
    except Exception as e:
        print(f"Fatal Error during initialization: {e}", file=sys.stderr)
        sys.exit(1)

    # --- Load Opening Book ---
    book_filename = f"{Position.WIDTH}x{Position.HEIGHT}.book"
    if os.path.exists(book_filename):
         solver.load_book(book_filename)
    else:
         print(f"Warning: Opening book '{book_filename}' not found.", file=sys.stderr)

    # --- Game Setup ---
    # Gán vai trò nhất quán, chỉ thay đổi người bắt đầu
    human_player_num = 1 # Người luôn là Player 1 trong thông báo lượt đi
    ai_player_num = 2    # AI luôn là Player 2 trong thông báo lượt đi

    if human_starts:
        current_player = human_player_num # Bắt đầu với Người
        print("\nHuman plays first (Player 1).")
    else:
        current_player = ai_player_num # Bắt đầu với AI
        print("\nAI plays first (Player 2).")


    game_over = False
    result = None

    # --- Game Loop ---
    while not game_over:
        display_board(p)

        if current_player == human_player_num:
            print(">>> Player 1's turn (Human) <<<")
            col_index = get_player_move(p)
            last_player_num = human_player_num # Người vừa đi
        else: # AI's turn
            print(">>> Player 2's turn (AI) <<<")
            col_index = get_ai_move(solver, p)
            if col_index == -1:
                 print("AI Error: Could not determine a move.", file=sys.stderr)
                 result = "Game Error"
                 game_over = True
                 continue

            print(f"AI chooses column {col_index + 1}")
            last_player_num = ai_player_num # AI vừa đi

        # Play the chosen column
        p.play_col(col_index)

        # Check if game is over
        # Quan trọng: Hàm check_game_over cần biết số của người chơi *vừa đi*
        result = check_game_over(p, last_player_num)
        if result:
            game_over = True
        else:
            # Switch to the other player (chuyển giữa 1 và 2)
            current_player = 3 - current_player

    # --- Game End ---
    print("\n" + "*"*30)
    print(" G A M E   O V E R")
    print("*"*30)
    display_board(p)
    print(f"Result: {result}")
    print("*"*30 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Play Connect 4 against an AI.")
    parser.add_argument('--ai-first', action='store_true', # Thêm tùy chọn --ai-first
                        help='Let the AI make the first move.')

    args = parser.parse_args() 

    play_game(human_starts=(not args.ai_first))