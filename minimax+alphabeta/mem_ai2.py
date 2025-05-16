import numpy as np
import pickle

class Board:
    def __init__(self):
        self.grid = np.zeros((6, 7), dtype=int)  # 0 = trống, 1 = người chơi 1, 2 = người chơi 2

    def drop_piece(self, column, player):
        if self.grid[0][column] == 0:  # Kiểm tra xem cột có đầy không
            for row in reversed(range(6)):
                if self.grid[row][column] == 0:
                    self.grid[row][column] = player
                    return True
        return False  # Cột đã đầy

    def is_full(self):
        return np.all(self.grid[0, :] != 0)

    def check_winner(self):
        for r in range(6):
            for c in range(7):
                if self.grid[r][c] != 0:
                    # Kiểm tra ngang
                    if c + 3 < 7 and all(self.grid[r][c] == self.grid[r][c + i] for i in range(4)):
                        return self.grid[r][c]
                    # Kiểm tra dọc
                    if r + 3 < 6 and all(self.grid[r][c] == self.grid[r + i][c] for i in range(4)):
                        return self.grid[r][c]
                    # Kiểm tra chéo xuống trái
                    if c + 3 < 7 and r + 3 < 6 and all(self.grid[r][c] == self.grid[r + i][c + i] for i in range(4)):
                        return self.grid[r][c]
                    # Kiểm tra chéo xuống phải
                    if c - 3 >= 0 and r + 3 < 6 and all(self.grid[r][c] == self.grid[r + i][c - i] for i in range(4)):
                        return self.grid[r][c]
        return 0

    def undo_move(self, column):
        for row in range(6):
            if self.grid[row][column] != 0:
                self.grid[row][column] = 0
                return

def evaluate_board(board):
    score = 0
    for r in range(6):
        for c in range(7):
            if board.grid[r][c] == 1:
                score += 1  # Điểm cho người chơi 1
            elif board.grid[r][c] == 2:
                score -= 1  # Điểm cho người chơi 2
    return score

def minimax(board, depth, alpha, beta, maximizing_player):
    winner = board.check_winner()
    if depth == 0 or board.is_full() or winner != 0:
        if winner == 1:
            return float('inf')  # AI 1 thắng
        elif winner == 2:
            return float('-inf')  # AI 2 thắng
        else:
            return evaluate_board(board)

    if maximizing_player:  # Chơi cho người chơi 1
        max_eval = float('-inf')
        for col in range(7):
            if board.drop_piece(col, 1):  # Assume player 1 is maximizing
                eval = minimax(board, depth - 1, alpha, beta, False)
                board.undo_move(col)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break  # Cắt bớt Beta
        return max_eval
    else:  # Chơi cho người chơi 2
        min_eval = float('inf')
        for col in range(7):
            if board.drop_piece(col, 2):  # Assume player 2 is minimizing
                eval = minimax(board, depth - 1, alpha, beta, True)
                board.undo_move(col)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break  # Cắt bớt Alpha
        return min_eval

def find_best_move(board, depth, player):
    best_move = -1
    best_value = float('-inf') if player == 1 else float('inf')
    for col in range(7):
        if board.drop_piece(col, player):  # AI là người chơi
            move_value = minimax(board, depth, float('-inf'), float('inf'), player == 1)
            board.undo_move(col)
            if (player == 1 and move_value > best_value) or (player == 2 and move_value < best_value):
                best_value = move_value
                best_move = col
    return best_move

def play_game():
    board = Board()
    current_player = 1  # Bắt đầu với AI 1
    while not board.is_full():
        print(board.grid)  # Hiển thị bảng hiện tại
        column = find_best_move(board, 5, current_player)  # AI sử dụng độ sâu hợp lý
        if column != -1:
            board.drop_piece(column, current_player)
            if board.check_winner() == 1:
                print("Người chơi 1 (AI 1) thắng!")
                break
            elif board.check_winner() == 2:
                print("Người chơi 2 (AI 2) thắng!")
                break
                
        current_player = 3 - current_player  # Chuyển đổi giữa người chơi 1 và 2

if __name__ == "__main__":
    while True:
        play_game()
        if input("Chơi lại? (y/n): ").lower() != 'y':
            break