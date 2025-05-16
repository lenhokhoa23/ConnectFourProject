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

    # Increased weight assignments
    if window.count(piece) == 4:
        score += 100  # AI win
    elif window.count(piece) == 3 and window.count(EMPTY) == 1:
        score += 5  # High score for three in a row
    elif window.count(piece) == 2 and window.count(EMPTY) == 2:
        score += 2  # Moderate score for two with space

    # Reducing score for opponent
    if window.count(opponent_piece) == 3 and window.count(EMPTY) == 1:
        score -= 4  # Block opponent's win
    if window.count(opponent_piece) == 2 and window.count(EMPTY) == 1:
        score -= 3  # Minor penalty for two 

    return score

def score_board(board):
    score = 0

    center_array = [int(i) for i in list(board[:, COLS // 2])]
    center_count = center_array.count(PLAYER_2)
    score += center_count * 3  # Center control feature

    for r in range(ROWS):
        row_array = [int(i) for i in list(board[r])]
        for c in range(COLS - 3):
            window = row_array[c:c + 4]
            score += evaluate_window(window, PLAYER_2)

    for c in range(COLS):
        column_array = [int(i) for i in list(board[:, c])]
        for r in range(ROWS - 3):
            window = column_array[r:r + 4]
            score += evaluate_window(window, PLAYER_2)

    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r + i][c + i] for i in range(4)]
            score += evaluate_window(window, PLAYER_2)

    for r in range(3, ROWS):
        for c in range(COLS - 3):
            window = [board[r - i][c + i] for i in range(4)]
            score += evaluate_window(window, PLAYER_2)

    return score

def minimax(board, depth, alpha, beta, maximizingPlayer):
    valid_locations = [c for c in range(COLS) if is_valid_location(board, c)]  # Corrected
    is_terminal = winning_move(board, PLAYER_1) or winning_move(board, PLAYER_2) or len(valid_locations) == 0

    if depth == 0 or is_terminal:
        if is_terminal:
            if winning_move(board, PLAYER_2):
                return (None, 100000000)  # AI wins
            elif winning_move(board, PLAYER_1):
                return (None, -100000000)  # Player wins
            else:
                return (None, 0)  # Tie
        else:
            return (None, score_board(board))  # Heuristic value

    if maximizingPlayer:
        value = -np.inf
        column = random.choice(valid_locations)
        for col in valid_locations:
            row = get_next_open_row(board, col)
            b_copy = board.copy()
            drop_piece(b_copy, row, col, PLAYER_2)
            new_score = minimax(b_copy, depth - 1, alpha, beta, False)[1]
            if new_score > value:
                value = new_score
                column = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return column, value
    else:  # Minimizing player
        value = np.inf
        column = random.choice(valid_locations)
        for col in valid_locations:
            row = get_next_open_row(board, col)
            b_copy = board.copy()
            drop_piece(b_copy, row, col, PLAYER_1)
            new_score = minimax(b_copy, depth - 1, alpha, beta, True)[1]
            if new_score < value:
                value = new_score
                column = col
            beta = min(beta, value)
            if beta <= alpha:
                break
        return column, value

def connect4_game():
    board = create_board()
    game_over = False
    turn = random.choice([PLAYER_1, PLAYER_2])  # Random start.
    
    # Set AI depth
    ai_depth = 7  # You can set this to a higher number (e.g., 6 or 7 or more) for smarter AI

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
            col, _ = minimax(board, ai_depth, -np.inf, np.inf, True)  # AI plays optimally.
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