import numpy as np
import random

ROWS = 6
COLS = 7
EMPTY = 0
PLAYER_1 = 1
PLAYER_2 = 2

def create_board():
    return np.zeros((ROWS, COLS), dtype=int)

def drop_piece(board, row, col, piece):
    board[row][col] = piece

def is_valid_location(board, col):
    return board[ROWS-1][col] == EMPTY

def get_next_open_row(board, col):
    for r in range(ROWS):
        if board[r][col] == EMPTY:
            return r

def print_board(board):
    print(np.flip(board, 0))

def winning_move(board, piece):
    # Checks for wins (horizontal, vertical, diagonal) as before
    for c in range(COLS-3):
        for r in range(ROWS):
            if (board[r][c] == piece and board[r][c+1] == piece and
                board[r][c+2] == piece and board[r][c+3] == piece):
                return True

    for c in range(COLS):
        for r in range(ROWS-3):
            if (board[r][c] == piece and board[r+1][c] == piece and
                board[r+2][c] == piece and board[r+3][c] == piece):
                return True

    for c in range(COLS-3):
        for r in range(ROWS-3):
            if (board[r][c] == piece and board[r+1][c+1] == piece and
                board[r+2][c+2] == piece and board[r+3][c+3] == piece):
                return True

    for c in range(COLS-3):
        for r in range(3, ROWS):
            if (board[r][c] == piece and board[r-1][c+1] == piece and
                board[r-2][c+2] == piece and board[r-3][c+3] == piece):
                return True

def evaluate_window(window, piece):
    score = 0
    opponent_piece = PLAYER_1 if piece == PLAYER_2 else PLAYER_2
    
    # Positive scores for our opportunities
    count_piece = window.count(piece)
    count_empty = window.count(EMPTY)
    
    if count_piece == 4:
        score += 100000
    elif count_piece == 3 and count_empty == 1:
        score += 500
    elif count_piece == 2 and count_empty == 2:
        score += 50
    elif count_piece == 1 and count_empty == 3:
        score += 1  # Small bonus for potential future opportunities
    
    # Negative scores for opponent threats
    count_opponent = window.count(opponent_piece)
    if count_opponent == 3 and count_empty == 1:
        score -= 1000  # Must block opponent's immediate win
    elif count_opponent == 2 and count_empty == 2:
        score -= 100  # Potential threat
    elif count_opponent == 1 and count_empty == 3:
        score -= 1  # Small penalty for opponent's potential
    
    return score

def score_board(board):
    score = 0
    
    # Prefer center column (more opportunities)
    center_array = [int(i) for i in list(board[:, COLS//2])]
    center_count = center_array.count(PLAYER_2)
    score += center_count * 6  # Increased center importance
    
    # Score horizontal
    for r in range(ROWS):
        row_array = [int(i) for i in list(board[r,:])]
        for c in range(COLS-3):
            window = row_array[c:c+4]
            score += evaluate_window(window, PLAYER_2)
    
    # Score vertical
    for c in range(COLS):
        col_array = [int(i) for i in list(board[:,c])]
        for r in range(ROWS-3):
            window = col_array[r:r+4]
            score += evaluate_window(window, PLAYER_2)
    
    # Score positive diagonal
    for r in range(ROWS-3):
        for c in range(COLS-3):
            window = [board[r+i][c+i] for i in range(4)]
            score += evaluate_window(window, PLAYER_2)
    
    # Score negative diagonal
    for r in range(3, ROWS):
        for c in range(COLS-3):
            window = [board[r-i][c+i] for i in range(4)]
            score += evaluate_window(window, PLAYER_2)
    
    # Additional positional advantages
    # Prefer columns that lead to multiple winning opportunities
    for c in range(COLS):
        if is_valid_location(board, c):
            row = get_next_open_row(board, c)
            # Check if this move creates multiple threats
            temp_board = board.copy()
            drop_piece(temp_board, row, c, PLAYER_2)
            if winning_move(temp_board, PLAYER_2):
                score += 10000  # Immediate win
            else:
                # Count how many winning paths this move opens
                winning_paths = count_winning_paths(temp_board, PLAYER_2)
                score += winning_paths * 10
    
    return score

def count_winning_paths(board, piece):
    count = 0
    
    # Check all possible 4-in-a-row paths
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS-3):
            window = board[r, c:c+4]
            # Convert to list and count
            piece_count = np.count_nonzero(window == piece)
            empty_count = np.count_nonzero(window == EMPTY)
            if piece_count + empty_count == 4 and piece_count >= 2:
                count += 1
    
    # Vertical
    for c in range(COLS):
        for r in range(ROWS-3):
            window = board[r:r+4, c]
            piece_count = np.count_nonzero(window == piece)
            empty_count = np.count_nonzero(window == EMPTY)
            if piece_count + empty_count == 4 and piece_count >= 2:
                count += 1
    
    # Positive diagonal
    for r in range(ROWS-3):
        for c in range(COLS-3):
            window = np.array([board[r+i, c+i] for i in range(4)])
            piece_count = np.count_nonzero(window == piece)
            empty_count = np.count_nonzero(window == EMPTY)
            if piece_count + empty_count == 4 and piece_count >= 2:
                count += 1
    
    # Negative diagonal
    for r in range(3, ROWS):
        for c in range(COLS-3):
            window = np.array([board[r-i, c+i] for i in range(4)])
            piece_count = np.count_nonzero(window == piece)
            empty_count = np.count_nonzero(window == EMPTY)
            if piece_count + empty_count == 4 and piece_count >= 2:
                count += 1
    
    return count

def minimax(board, depth, alpha, beta, maximizingPlayer):
    valid_locations = get_valid_locations(board)
    is_terminal = is_terminal_node(board)
    
    if depth == 0 or is_terminal:
        if is_terminal:
            if winning_move(board, PLAYER_2):
                return (None, 100000000)
            elif winning_move(board, PLAYER_1):
                return (None, -100000000)
            else:  # Game is over, no more valid moves
                return (None, 0)
        else:  # Depth is zero
            return (None, score_board(board))
    
    # Move ordering - try center columns first
    valid_locations.sort(key=lambda x: abs(x - COLS//2))
    
    if maximizingPlayer:
        value = -np.inf
        column = valid_locations[0]
        for col in valid_locations:
            row = get_next_open_row(board, col)
            b_copy = board.copy()
            drop_piece(b_copy, row, col, PLAYER_2)
            new_score = minimax(b_copy, depth-1, alpha, beta, False)[1]
            if new_score > value:
                value = new_score
                column = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return column, value
    
    else:  # Minimizing player
        value = np.inf
        column = valid_locations[0]
        for col in valid_locations:
            row = get_next_open_row(board, col)
            b_copy = board.copy()
            drop_piece(b_copy, row, col, PLAYER_1)
            new_score = minimax(b_copy, depth-1, alpha, beta, True)[1]
            if new_score < value:
                value = new_score
                column = col
            beta = min(beta, value)
            if beta <= alpha:
                break
        return column, value

def get_valid_locations(board):
    return [c for c in range(COLS) if is_valid_location(board, c)]

def is_terminal_node(board):
    return (winning_move(board, PLAYER_1) or 
            winning_move(board, PLAYER_2) or 
            len(get_valid_locations(board)) == 0)

def find_best_move(board, max_depth=7):
    best_score = -np.inf
    best_col = random.choice(get_valid_locations(board))
    
    # Iterative deepening
    for depth in range(1, max_depth+1):
        column, score = minimax(board, depth, -np.inf, np.inf, True)
        if score > best_score:
            best_score = score
            best_col = column
            # Early exit if we find a winning move
            if best_score >= 100000:
                break
    return best_col

def connect4_game():
    board = create_board()
    game_over = False
    turn = random.choice([PLAYER_1, PLAYER_2])  # Random start.
    
    # Set AI depth
    ai_depth = 6

    while not game_over:
        if turn == PLAYER_1:  # Player 1's turn
            col = int(input("Player 1 Make your Selection (0-6): "))
            if is_valid_location(board, col):
                row = get_next_open_row(board, col)
                drop_piece(board, row, col, PLAYER_1)

                if winning_move(board, PLAYER_1):
                    print_board(board)
                    print("Player 1 wins!")
                    game_over = True
        else:  # AI's turn
            col = find_best_move(board, ai_depth)
            if is_valid_location(board, col):
                print(f"AI selects column: {col}")  # Show AI's selected column
                row = get_next_open_row(board, col)
                drop_piece(board, row, col, PLAYER_2)

                if winning_move(board, PLAYER_2):
                    print_board(board)
                    print("AI wins!")
                    game_over = True

        print_board(board)

        # Check for draw condition
        if not game_over and np.all(board != EMPTY):
            print("The game is a draw!")
            game_over = True

        turn = PLAYER_1 if turn == PLAYER_2 else PLAYER_2  # Switch turns
        
if __name__ == "__main__":
    connect4_game()