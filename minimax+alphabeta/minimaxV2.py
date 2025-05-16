import random
import copy

ROWS = 6
COLS = 7
WINDOW_LENGTH = 4

# Quân cờ
EMPTY = 0
PLAYER = 1
AI = 2
OTHER = 3  # Quân của ô ẩn

def create_board():
    return [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]

def print_board(board):
    print(" 0 1 2 3 4 5 6")
    for r in range(ROWS):
        row_str = ""
        for c in range(COLS):
            cell = board[r][c]
            if cell == EMPTY:
                row_str += "| "
            elif cell == PLAYER:
                row_str += "|X"
            elif cell == AI:
                row_str += "|O"
            elif cell == OTHER:
                row_str += "|*"
        row_str += "|"
        print(row_str)
    print("-" * (COLS * 2 + 1))

def is_valid_location(board, col):
    return board[0][col] == EMPTY

def get_next_open_row(board, col):
    for r in range(ROWS-1, -1, -1):
        if board[r][col] == EMPTY:
            return r
    return None

def drop_piece(board, row, col, piece):
    board[row][col] = piece

def winning_move(board, piece):
    # Kiểm tra theo chiều dọc
    for c in range(COLS):
        for r in range(ROWS - 3):
            if all(board[r+i][c] == piece for i in range(4)):
                return True
    # Kiểm tra theo chiều ngang
    for r in range(ROWS):
        for c in range(COLS - 3):
            if all(board[r][c+i] == piece for i in range(4)):
                return True
    # Đường chéo /
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if all(board[r-i][c+i] == piece for i in range(4)):
                return True
    # Đường chéo \
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if all(board[r+i][c+i] == piece for i in range(4)):
                return True
    return False

def get_valid_locations(board):
    return [c for c in range(COLS) if is_valid_location(board, c)]

def is_terminal_node(board):
    return winning_move(board, PLAYER) or winning_move(board, AI) or len(get_valid_locations(board)) == 0

# Hàm đánh giá vị trí
def evaluate_window(window, piece):
    score = 0
    opp_piece = PLAYER if piece == AI else AI

    if window.count(piece) == 4:
        score += 100
    elif window.count(piece) == 3 and window.count(EMPTY) == 1:
        score += 5
    elif window.count(piece) == 2 and window.count(EMPTY) == 2:
        score += 2

    if window.count(opp_piece) == 3 and window.count(EMPTY) == 1:
        score -= 4

    return score

def score_position(board, piece):
    score = 0

    # Ưu tiên trung tâm cột
    center_array = [board[r][COLS//2] for r in range(ROWS)]
    center_count = center_array.count(piece)
    score += center_count * 3

    # Đánh giá theo hàng
    for r in range(ROWS):
        row_array = [board[r][c] for c in range(COLS)]
        for c in range(COLS - 3):
            window = row_array[c:c+4]
            score += evaluate_window(window, piece)

    # Đánh giá theo cột
    for c in range(COLS):
        col_array = [board[r][c] for r in range(ROWS)]
        for r in range(ROWS - 3):
            window = col_array[r:r+4]
            score += evaluate_window(window, piece)

    # Đường chéo /
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r+i][c+i] for i in range(4)]
            score += evaluate_window(window, piece)

    # Đường chéo \
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            window = [board[r-i][c+i] for i in range(4)]
            score += evaluate_window(window, piece)

    return score

# Minimax tối ưu hơn với cắt tỉa alpha-beta
def minimax(board, depth, alpha, beta, maximizingPlayer):
    valid_locations = get_valid_locations(board)
    is_terminal = is_terminal_node(board)

    if depth == 0 or is_terminal:
        if is_terminal:
            if winning_move(board, AI):
                return (None, 1e9)
            elif winning_move(board, PLAYER):
                return (None, -1e9)
            else:
                return (None, 0)
        else:
            return (None, score_position(board, AI))
    if maximizingPlayer:
        value = -float('inf')
        best_col = random.choice(valid_locations)
        for col in valid_locations:
            b_copy = copy.deepcopy(board)
            row = get_next_open_row(b_copy, col)
            drop_piece(b_copy, row, col, AI)
            new_score = minimax(b_copy, depth-1, alpha, beta, False)[1]
            if new_score > value:
                value = new_score
                best_col = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return best_col, value
    else:
        value = float('inf')
        best_col = random.choice(valid_locations)
        for col in valid_locations:
            b_copy = copy.deepcopy(board)
            row = get_next_open_row(b_copy, col)
            drop_piece(b_copy, row, col, PLAYER)
            new_score = minimax(b_copy, depth-1, alpha, beta, True)[1]
            if new_score < value:
                value = new_score
                best_col = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return best_col, value

def main():
    board = create_board()
    print("Chào mừng bạn đến với game Connect 4 có ô ẩn!")

    # Chọn ai đánh trước
    while True:
        turn_choice = input("Nhập 'a' để bạn đánh trước, 'b' để AI đánh trước: ").lower()
        if turn_choice in ['a', 'b']:
            break
        else:
            print("Vui lòng nhập đúng (a hoặc b).")
    turn = 0 if turn_choice == 'a' else 1

    # Chọn ô ẩn
    hidden_cells = []
    print("Bạn có thể chọn 2 ô ẩn ban đầu (tối đa 2 ô).")
    for i in range(2):
        while True:
            try:
                print(f"Chọn ô ẩn thứ {i+1}:")
                r = int(input(f"Nhập hàng (0-{ROWS-1}): "))
                c = int(input(f"Nhập cột (0-{COLS-1}): "))
                if 0 <= r < ROWS and 0 <= c < COLS:
                    if (r, c) not in hidden_cells:
                        hidden_cells.append((r, c))
                        break
                    else:
                        print("Ô này đã được chọn rồi, chọn ô khác.")
                else:
                    print("Vui lòng nhập đúng phạm vi.")
            except:
                print("Vui lòng nhập số hợp lệ.")
    # Đặt quân ô ẩn
    for (r, c) in hidden_cells:
        board[r][c] = OTHER

    print("Các ô ẩn đã chứa quân của bên thứ 3 tại các vị trí:", hidden_cells)
    print_board(board)

    game_over = False

    while not game_over:
        if turn == 0:
            # Người chơi
            valid_choice = False
            while not valid_choice:
                try:
                    col = int(input("Bạn chọn cột (0-6): "))
                    if col in get_valid_locations(board):
                        row = get_next_open_row(board, col)
                        drop_piece(board, row, col, PLAYER)
                        valid_choice = True
                    else:
                        print("Cột không hợp lệ hoặc đầy, vui lòng chọn lại.")
                except:
                    print("Vui lòng nhập số hợp lệ.")
            if winning_move(board, PLAYER):
                print_board(board)
                print("Chúc mừng! Bạn thắng rồi!")
                game_over = True
        else:
            # AI
            print("AI đang suy nghĩ...")
            col, minimax_score = minimax(board, 8, -1e9, 1e9, True)
            if col is not None:
                row = get_next_open_row(board, col)
                drop_piece(board, row, col, AI)
                if winning_move(board, AI):
                    print_board(board)
                    print("AI thắng rồi! Thật tiếc.")
                    game_over = True

        print_board(board)

        if len(get_valid_locations(board)) == 0 and not game_over:
            print("Hòa rồi!")
            game_over = True

        turn = (turn + 1) % 2

if __name__ == "__main__":
    main()