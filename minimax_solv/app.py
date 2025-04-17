# File: app.py (Phiên bản sửa lỗi chuyển đổi board và thêm log)

from fastapi import FastAPI, HTTPException
import random
import uvicorn
import os
import sys
from pydantic import BaseModel
from typing import List, Optional
import math # Thêm import math nếu dùng ceil

try:
    if '.' not in sys.path:
         script_dir = os.path.dirname(__file__)
         if script_dir:
              sys.path.insert(0, script_dir)
    from position import Position
    from solver import Solver
except ImportError as e:
    print(f"CRITICAL ERROR: Could not import AI modules: {e}", file=sys.stderr)
    sys.exit(1)
except FileNotFoundError:
    print("CRITICAL ERROR: Error determining script directory.", file=sys.stderr)
    sys.exit(1)
except Exception as ex:
    print(f"CRITICAL ERROR: An unexpected error occurred during AI module import: {ex}", file=sys.stderr)
    sys.exit(1)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GameState(BaseModel):
    board: List[List[int]]
    current_player: int
    valid_moves: List[int]

class AIResponse(BaseModel):
    move: int

print("Initializing AI Solver...", file=sys.stderr)
try:
    solver = Solver()
    book_filename = f"{Position.WIDTH}x{Position.HEIGHT}.book"
    if os.path.exists(book_filename):
        solver.load_book(book_filename)
    else:
        print(f"Warning: Opening book '{book_filename}' not found.", file=sys.stderr)
    print("AI Solver initialized successfully.", file=sys.stderr)
except Exception as e:
    print(f"CRITICAL ERROR: Failed to initialize AI Solver: {e}", file=sys.stderr)
    solver = None

@app.post("/api/connect4-move", response_model=AIResponse)
async def make_move(game_state: GameState) -> AIResponse:
    if solver is None:
         raise HTTPException(status_code=500, detail="AI Solver is not available.")

    print(f"\n=== Request Received ===", file=sys.stderr)
    print(f"Player Turn: {game_state.current_player}", file=sys.stderr)
    print(f"Valid Moves: {game_state.valid_moves}", file=sys.stderr)
    print(f"Board Received (API format - top row first?):", file=sys.stderr)
    for r, row in enumerate(game_state.board):
        print(f"  Row {r}: {row}", file=sys.stderr)
    print("-" * 20, file=sys.stderr)


    try:
        if not game_state.valid_moves:
            print("Error: Received request with no valid moves.", file=sys.stderr)
            raise ValueError("No valid moves available")

        # === Sửa đổi phần chuyển đổi board ===
        board_list = game_state.board
        api_current_player = game_state.current_player
        if not (1 <= api_current_player <= 2):
             raise ValueError(f"Invalid current_player value: {api_current_player}")

        pos = Position()
        player1_mask = 0
        player2_mask = 0
        moves_count = 0

        if len(board_list) != Position.HEIGHT or len(board_list[0]) != Position.WIDTH:
             raise ValueError(f"Invalid board dimensions: {len(board_list)}x{len(board_list[0]) if board_list else 'N/A'}")

        # --- Giả định API board_list[0] là hàng TRÊN CÙNG ---
        print("Converting API board (assuming top-down) to bitboard (bottom-up)...", file=sys.stderr)
        for r_api in range(Position.HEIGHT):
            for c in range(Position.WIDTH):
                # Chuyển đổi index hàng API (0=top) sang index hàng bitboard (0=bottom)
                r_internal = Position.HEIGHT - 1 - r_api

                player_num = board_list[r_api][c] # Lấy từ API board
                if player_num != 0:
                    # Tính bitmask với index hàng internal
                    cell_mask = 1 << (r_internal + c * (Position.HEIGHT + 1))
                    pos.mask |= cell_mask
                    moves_count += 1
                    if player_num == 1:
                        player1_mask |= cell_mask
                    elif player_num == 2:
                        player2_mask |= cell_mask

        pos.moves = moves_count
        if api_current_player == 1:
            pos.current_position = player1_mask
        else:
            pos.current_position = player2_mask
        # ---------------------------------------

        print(f"Converted Position Object:", file=sys.stderr)
        print(f"  Moves: {pos.moves}", file=sys.stderr)
        print(f"  Mask: {bin(pos.mask)}", file=sys.stderr)
        print(f"  CurrentPos (P{api_current_player}'s stones): {bin(pos.current_position)}", file=sys.stderr)
        print(f"  Board Representation:\n{pos}", file=sys.stderr) # In ra bàn cờ dạng text của Position
        print("-" * 20, file=sys.stderr)


        # Gọi Solver
        print("Analyzing position with solver...", file=sys.stderr)
        scores = solver.analyze(pos, weak=False)
        print(f"AI Raw Scores: {scores}", file=sys.stderr)

        # Chọn nước đi tốt nhất
        best_score = -float('inf')
        best_moves = []

        print(f"Evaluating valid moves from request: {game_state.valid_moves}", file=sys.stderr)
        for valid_col in game_state.valid_moves:
            if 0 <= valid_col < Position.WIDTH:
                score = scores[valid_col]
                print(f"  Col {valid_col+1}: Score={score}", file=sys.stderr) # Log điểm từng cột hợp lệ
                if score != Solver.INVALID_MOVE: # Chỉ xem xét các nước hợp lệ theo solver
                    if score > best_score:
                        best_score = score
                        best_moves = [valid_col]
                        print(f"    New best score found!", file=sys.stderr)
                    elif score == best_score:
                        best_moves.append(valid_col)
                        print(f"    Equal best score.", file=sys.stderr)
            else:
                 print(f"  Warning: Skipping invalid column {valid_col} from valid_moves list.", file=sys.stderr)


        if not best_moves:
            print(f"Error: AI could not find any valid moves among {game_state.valid_moves} with scores {scores}. Falling back.", file=sys.stderr)
            if game_state.valid_moves:
                 selected_move = game_state.valid_moves[0]
                 print(f"Falling back to first valid move: {selected_move}", file=sys.stderr)
            else:
                 raise ValueError("No valid moves available and AI failed.")
        else:
            selected_move = random.choice(best_moves)
            print(f"AI analysis complete. Best score: {best_score}. Recommended moves: {[m+1 for m in best_moves]}. Chosen column index: {selected_move}", file=sys.stderr)

        print(f"=== Sending Response: {{'move': {selected_move}}} ===", file=sys.stderr)
        return AIResponse(move=selected_move)

    # --- Xử lý lỗi (giữ nguyên hoặc cải thiện) ---
    except ValueError as ve:
        print(f"ValueError in make_move: {ve}", file=sys.stderr)
        if game_state.valid_moves:
            selected_move = game_state.valid_moves[0]
            print(f"Falling back to first valid move {selected_move} due to error.", file=sys.stderr)
            return AIResponse(move=selected_move)
        else:
            raise HTTPException(status_code=400, detail=f"Client Error: {ve} and no valid moves.")
    except Exception as e:
        print(f"Unexpected error in make_move: {type(e).__name__} - {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        if game_state.valid_moves:
             selected_move = game_state.valid_moves[0]
             print(f"Falling back to first valid move {selected_move} due to internal error.", file=sys.stderr)
             return AIResponse(move=selected_move)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {type(e).__name__}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting Connect4 AI server on host 0.0.0.0:{port}", file=sys.stderr)
    uvicorn.run(app, host="0.0.0.0", port=port)