from fastapi import FastAPI, HTTPException, Body
import random
import uvicorn
import os
import subprocess
from pydantic import BaseModel
from typing import List, Optional, Tuple # Tuple cần cho type hint của removed_cells
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys 
import time 

# --- Cấu hình C++ Process ---
C_PROCESS_EXEC = "./InteractiveSolver.exe" # Đặt tên file thực thi C++ mới của bạn
cpp_process: Optional[subprocess.Popen] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global cpp_process
    print(f"App startup: Starting C++ process {C_PROCESS_EXEC}...")
    cpp_ready = False
    try:
        cpp_process = subprocess.Popen(
            [C_PROCESS_EXEC],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, 
            text=True,
            bufsize=1,
            universal_newlines=True # Đảm bảo xử lý newline đúng cách trên các OS
        )
        print(f"C++ process started with PID: {cpp_process.pid}")

        timeout_start = time.time()
        startup_timeout = 15 # Timeout cho C++ process khởi động

        while time.time() - timeout_start < startup_timeout:
            if cpp_process.stderr is None: # Kiểm tra nếu stderr là None
                print("C++ process stderr is None, cannot readline.", file=sys.stderr)
                break
            
            line = cpp_process.stderr.readline().strip()
            if not line:
                if cpp_process.poll() is not None:
                    print("C++ process exited prematurely during startup (no stderr output).", file=sys.stderr)
                    stdout_dump = cpp_process.stdout.read() if cpp_process.stdout else ""
                    if stdout_dump: print(f"C++ STDOUT DUMP ON FAILURE: {stdout_dump}", file=sys.stderr)
                    cpp_process = None # Đánh dấu là đã dừng
                    break
                time.sleep(0.1) 
                continue

            print(f"C++_STDERR: {line}", file=sys.stderr) 
            if "READY" in line:
                print("C++ process reported READY.")
                cpp_ready = True
                break
            if "FATAL_ERROR" in line.upper() or "ERROR" in line.upper(): 
                print("C++ process reported an error during startup.", file=sys.stderr)
                break
            if cpp_process.poll() is not None: 
                print("C++ process exited prematurely during startup (after stderr line).", file=sys.stderr)
                cpp_process = None # Đánh dấu là đã dừng
                break
        
        if not cpp_ready:
            print("C++ process failed to report READY or reported an error. AI service might be unavailable.", file=sys.stderr)
            if cpp_process and cpp_process.poll() is None:
                print("C++ process is still running but did not signal READY. Killing.", file=sys.stderr)
                try: cpp_process.kill()
                except Exception: pass
            cpp_process = None

    except FileNotFoundError:
        print(f"FATAL ERROR: C++ executable not found at {C_PROCESS_EXEC}. Build it or check path.", file=sys.stderr)
        cpp_process = None
    except Exception as e:
        print(f"An error occurred while starting C++ process: {e}", file=sys.stderr)
        if cpp_process and cpp_process.poll() is None:
            try: cpp_process.kill()
            except Exception: pass
        cpp_process = None
    
    yield 

    print("App shutdown: Stopping C++ process...")
    if cpp_process and cpp_process.poll() is None:
        try:
            cpp_process.stdin.write("QUIT\n")
            cpp_process.stdin.flush()
            cpp_process.wait(timeout=5)
            print("C++ process stopped gracefully.", file=sys.stderr)
        except Exception as e:
            print(f"Error stopping C++ process gracefully: {e}. Killing it.", file=sys.stderr)
            try: cpp_process.kill()
            except Exception as e_kill: print(f"Error killing C++ process: {e_kill}", file=sys.stderr)
    print("App shutdown complete.")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Cho phép tất cả các origin (thay đổi thành domain của bạn trong production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/api/test")
async def health_check():
    return {"status": "ok", "message": "Server is running"}
# Định nghĩa model cho request từ client (frontend)
class AIPlayRequest(BaseModel):
    board: List[List[int]] # 0: empty, 1: Player 1 (X), 2: Player 2 (O), -1: removed cell
    player_to_move: int    # 1 hoặc 2, là người chơi mà AI cần tính nước đi cho
    # removed_cells_coordinates: List[Tuple[int, int]] # List của các cặp (row, col) 0-indexed

class AIResponse(BaseModel):
    move: int # Cột AI chọn (0-6)
    # scores: Optional[List[int]] = None # Tùy chọn: trả về vector điểm nếu muốn

@app.post("/api/get_ai_move", response_model=AIResponse)
async def get_ai_move_endpoint(request_data: AIPlayRequest = Body(...)):
    start_time_req = time.time()

    if cpp_process is None or cpp_process.poll() is not None:
        print("C++ process is not running. Cannot get AI move.", file=sys.stderr)
        raise HTTPException(status_code=503, detail="AI service backend not available.")

    # --- Xác định các ô bị chặn từ board input ---
    removed_cells_found: List[Tuple[int, int]] = []
    for r_idx, row_content in enumerate(request_data.board):
        for c_idx, cell_val in enumerate(row_content):
            if cell_val == -1:
                removed_cells_found.append((r_idx, c_idx))
    
    if len(removed_cells_found) != 2:

        print(f"Warning/Error: Expected 2 removed cells (-1) in board, found {len(removed_cells_found)}. Adjusting.", file=sys.stderr)
        if len(removed_cells_found) == 1:
            r1, c1 = removed_cells_found[0]
            r2, c2 = r1, c1 # Gửi tọa độ trùng nhau
        elif len(removed_cells_found) == 0:
             # Gửi một cặp không ảnh hưởng nhiều (ví dụ ngoài rìa), hoặc (0,0)-(0,0) nếu sách của bạn dùng nó
            r1, c1, r2, c2 = 0,0,0,0 
        else: # Nhiều hơn 2 ô, lấy 2 ô đầu tiên
            r1, c1 = removed_cells_found[0]
            r2, c2 = removed_cells_found[1]
    else:
        r1, c1 = removed_cells_found[0]
        r2, c2 = removed_cells_found[1]
    # ------------------------------------------

    try:

        cpp_process.stdin.write("GET_MOVE\n")
        cpp_process.stdin.write(f"{r1} {c1} {r2} {c2}\n")
        cpp_process.stdin.write(f"{request_data.player_to_move}\n")
        
        board_to_send_str = ""
        for r_idx, row_content in enumerate(request_data.board):
            # Chuyển -1 (ô bị chặn) thành 0 (ô trống) khi gửi cho C++ reconstructPosition,
            # vì C++ Position đã được khởi tạo với thông tin ô bị chặn riêng.
            processed_row = [str(0) if cell == -1 else str(cell) for cell in row_content]
            board_to_send_str += " ".join(processed_row) + "\n"
        cpp_process.stdin.write(board_to_send_str)
        cpp_process.stdin.flush()
        
        print(f"Sent GET_MOVE to C++ for player {request_data.player_to_move} with removed ({r1},{c1}) & ({r2},{c2})", file=sys.stderr)

        response_line = cpp_process.stdout.readline().strip()
        print(f"Received from C++: '{response_line}'", file=sys.stderr)

        if response_line.startswith("MOVE "):
            try:
                selected_move = int(response_line.split(" ")[1])
                # TODO: Client nên tự kiểm tra selected_move có trong valid_moves của nó không.
                # Hoặc C++ cần đảm bảo trả về nước đi hợp lệ từ danh sách nó tự tính.
                # Hiện tại, C++ Solver::analyze nên đã trả về nước đi hợp lệ.
                print(f"AI (Player {request_data.player_to_move}) chose column: {selected_move}", file=sys.stderr)
                return AIResponse(move=selected_move)
            except (ValueError, IndexError):
                print(f"Error parsing MOVE from C++: '{response_line}'", file=sys.stderr)
                raise HTTPException(status_code=500, detail="AI returned invalid move format.")
        elif response_line.startswith("ERROR"):
            print(f"C++ process reported an error: {response_line}", file=sys.stderr)
            raise HTTPException(status_code=500, detail=f"AI calculation error: {response_line}")
        else:
            print(f"Unexpected response from C++: '{response_line}'", file=sys.stderr)
            raise HTTPException(status_code=500, detail="AI returned unexpected response.")

    except Exception as e:
        print(f"An unexpected error occurred in get_ai_move_endpoint: {e}", file=sys.stderr)
        # Cố gắng đọc thêm output từ C++ để debug
        stderr_dump = ""
        if cpp_process and cpp_process.stderr :
            try:
                # Set stderr to non-blocking
                fd = cpp_process.stderr.fileno()
                fl = os.fcntl(fd, os.F_GETFL)
                os.fcntl(fd, os.F_SETFL, fl | os.O_NONBLOCK)
                stderr_dump = cpp_process.stderr.read()
            except: # Bỏ qua lỗi nếu không đọc được
                 pass 
        if stderr_dump: print(f"C++ STDERR during error: {stderr_dump}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        end_time_req = time.time()
        print(f"Total request processing time: {(end_time_req - start_time_req)*1000:.2f} ms", file=sys.stderr)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000)) 
    print(f"Starting Uvicorn server on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)