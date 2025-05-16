import numpy as np

# Constants for the game
ROW_COUNT = 6
COLUMN_COUNT = 7
PLAYER_1 = 1
PLAYER_2 = 2

def create_board():
    return np.zeros((ROW_COUNT, COLUMN_COUNT))

def drop_piece(board, row, col, piece):
    board[row][col] = piece

def is_valid_location(board, col):
    return board[ROW_COUNT-1][col] == 0

def get_next_open_row(board, col):
    for r in range(ROW_COUNT):
        if board[r][col] == 0:
            return r

def print_board(board):
    print(np.flip(board, 0))

def winning_move(board, piece):
    # Check horizontal locations for win
    for c in range(COLUMN_COUNT-3):
        for r in range(ROW_COUNT):
            if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
                return True

    # Check vertical locations for win
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT-3):
            if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
                return True

    # Check positively sloped diagonals
    for c in range(COLUMN_COUNT-3):
        for r in range(ROW_COUNT-3):
            if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                return True

    # Check negatively sloped diagonals
    for c in range(COLUMN_COUNT-3):
        for r in range(3, ROW_COUNT):
            if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                return True

def check_draw(board):
    # Check if the board is full
    return all(board[ROW_COUNT - 1][c] != 0 for c in range(COLUMN_COUNT))

def ai_move(board, player_piece):
    # Check to block opponent's winning move
    opponent_piece = PLAYER_1 if player_piece == PLAYER_2 else PLAYER_2
    for col in range(COLUMN_COUNT):
        if is_valid_location(board, col):
            row = get_next_open_row(board, col)
            drop_piece(board, row, col, opponent_piece)
            if winning_move(board, opponent_piece):
                board[row][col] = 0  # remove the piece
                return col  # Block the move
            board[row][col] = 0  # remove the piece

    # Check for own winning move
    for col in range(COLUMN_COUNT):
        if is_valid_location(board, col):
            row = get_next_open_row(board, col)
            drop_piece(board, row, col, player_piece)
            if winning_move(board, player_piece):
                return col
            board[row][col] = 0  # remove the piece

    # Favor the center column
    if is_valid_location(board, COLUMN_COUNT // 2):
        return COLUMN_COUNT // 2

    # Random move (fallback)
    col = np.random.randint(0, COLUMN_COUNT)
    while not is_valid_location(board, col):
        col = np.random.randint(0, COLUMN_COUNT)
    return col

# Example of how to use the AI
if __name__ == "__main__":
    board = create_board()
    game_over = False
    turn = 0

    while not game_over:
        if turn == 0:  # Player 1
            col = int(input("Player 1 Make your Selection (0-6):"))
            if is_valid_location(board, col):
                row = get_next_open_row(board, col)
                drop_piece(board, row, col, PLAYER_1)
                if winning_move(board, PLAYER_1):
                    print_board(board)
                    print("Player 1 wins!")
                    game_over = True
        else:  # AI - Player 2
            col = ai_move(board, PLAYER_2)
            if is_valid_location(board, col):
                row = get_next_open_row(board, col)
                drop_piece(board, row, col, PLAYER_2)
                if winning_move(board, PLAYER_2):
                    print_board(board)
                    print("Player 2 wins!")
                    game_over = True

        print_board(board)

        # Check for a draw after each turn
        if check_draw(board):
            print("It's a draw!")
            game_over = True

        # Switch turns
        turn += 1
        turn = turn % 2  # Alternate turns between Player 1 and AI