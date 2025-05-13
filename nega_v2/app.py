from fastapi import FastAPI, HTTPException, Body
import random # Giữ lại để có thể dùng làm fallback nếu cần thiết nhất
import uvicorn
import os
import subprocess
from pydantic import BaseModel
from typing import List, Optional, Tuple 
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys 
import time 
import fcntl # Thêm import này cho non-blocking stderr read trên Linux/macOS

# --- Cấu hình C++ Process ---
C_PROCESS_EXEC = "./InteractiveSolver" # Tên file thực thi C++ của bạn (đã được build bởi Dockerfile)
cpp_process: Optional[subprocess.Popen] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global cpp_process
    print(f"App startup: Starting C++ process {C_PROCESS_EXEC}...")
    cpp_ready = False
    try:
        # Thiết lập môi trường để stdout/stderr của Python không bị buffer (nếu cần thiết)
        # os.environ['PYTHONUNBUFFERED'] = '1' # Đã set trong Dockerfile, không cần ở đây

        cpp_process = subprocess.Popen(
            [C_PROCESS_EXEC],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, 
            text=True, # Giúp làm việc với string dễ hơn
            bufsize=1, # Line buffering
            universal_newlines=True # Xử lý các loại newline
        )
        print(f"C++ process started with PID: {cpp_process.pid}")

        # Đặt stderr của C++ process ở chế độ non-blocking để readline không bị kẹt
        if cpp_process.stderr:
            fd = cpp_process.stderr.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        timeout_start = time.time()
        startup_timeout = 20 # Tăng timeout một chút cho C++ khởi động và báo READY

        while time.time() - timeout_start < startup_timeout:
            if cpp_process.poll() is not None: # Kiểm tra process có thoát sớm không
                print("C++ process exited prematurely during startup.", file=sys.stderr)
                # Đọc phần còn lại của stdout và stderr nếu có
                stdout_dump = cpp_process.stdout.read() if cpp_process.stdout else ""
                stderr_dump = cpp_process.stderr.read() if cpp_process.stderr else "" # Đọc từ non-blocking stderr
                if stdout_dump: print(f"C++ STDOUT DUMP ON FAILURE: {stdout_dump}", file=sys.stderr)
                if stderr_dump: print(f"C++ STDERR DUMP ON FAILURE: {stderr_dump}", file=sys.stderr)
                cpp_process = None 
                break

            line = ""
            if cpp_process.stderr: # Chỉ đọc nếu stderr tồn tại
                try:
                    line = cpp_process.stderr.readline().strip()
                except BlockingIOError: # Xảy ra nếu không có gì để đọc ở non-blocking mode
                    time.sleep(0.1) # Chờ một chút rồi thử lại
                    continue 
                except Exception as e_read:
                    print(f"Exception reading stderr: {e_read}", file=sys.stderr)
                    time.sleep(0.1)
                    continue
            
            if line: # Nếu đọc được một dòng
                print(f"C++_STDERR: {line}", file=sys.stderr) 
                if "READY" in line:
                    print("C++ process reported READY.")
                    cpp_ready = True
                    break
                if "FATAL_ERROR" in line.upper() or "ERROR:" in line.upper(): # Thêm "ERROR:" để bắt lỗi chung
                    print("C++ process reported an error during startup via stderr.", file=sys.stderr)
                    break 
            else: # Nếu không đọc được dòng nào (readline trả về rỗng) và process chưa thoát
                time.sleep(0.1) # Chờ một chút

        if not cpp_ready:
            print("C++ process failed to report READY or reported an error within timeout. AI service might be unavailable.", file=sys.stderr)
            if cpp_process and cpp_process.poll() is None:
                print("C++ process is still running but did not signal READY. Killing.", file=sys.stderr)
                try: cpp_process.kill()
                except Exception: pass
            cpp_process = None

    except FileNotFoundError:
        print(f"FATAL ERROR: C++ executable not found at {C_PROCESS_EXEC}. Ensure it's built and path is correct in Dockerfile.", file=sys.stderr)
        cpp_process = None
    except Exception as e:
        print(f"An error occurred while starting C++ process: {e}", file=sys.stderr)
        if cpp_process and cpp_process.poll() is None:
            try: cpp_process.kill()
            except Exception: pass
        cpp_process = None
    
    yield # Ứng dụng FastAPI chính chạy ở đây

    print("App shutdown: Stopping C++ process...")
    if cpp_process and cpp_process.poll() is None:
        try:
            if cpp_process.stdin:
                cpp_process.stdin.write("QUIT\n")
                cpp_process.stdin.flush()
            cpp_process.wait(timeout=5) # Chờ tối đa 5 giây
            print("C++ process stopped gracefully.", file=sys.stderr)
        except subprocess.TimeoutExpired:
            print(f"C++ process did not exit after QUIT command and 5s timeout. Killing.", file=sys.stderr)
            try: cpp_process.kill()
            except Exception as e_kill: print(f"Error killing C++ process: {e_kill}", file=sys.stderr)
        except Exception as e: # Các lỗi khác khi gửi QUIT hoặc flush
            print(f"Error stopping C++ process gracefully: {e}. Attempting to kill.", file=sys.stderr)
            try: cpp_process.kill()
            except Exception as e_kill: print(f"Error killing C++ process: {e_kill}", file=sys.stderr)
    print("App shutdown complete.")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/test")
async def health_check():
    if cpp_process and cpp_process.poll() is None:
        return {"status": "ok", "message": "Python server is running and C++ process is active."}
    elif cpp_process and cpp_process.poll() is not None:
        return {"status": "error", "message": "Python server is running but C++ process has exited."}
    else:
        return {"status": "error", "message": "Python server is running but C++ process is not available/failed to start."}


# Model cho request từ client, khớp với GameState bạn cung cấp
class GameStateRequest(BaseModel):
    board: List[List[int]] 
    current_player: int    
    valid_moves: Optional[List[int]] = None # Giữ lại nếu client có gửi, nhưng không bắt buộc

class AIResponse(BaseModel):
    move: int 

@app.post("/api/get_ai_move", response_model=AIResponse)
async def get_ai_move_endpoint(request_data: GameStateRequest = Body(...)):
    request_received_time = time.time()
    print(f"Received request for /api/get_ai_move for player {request_data.current_player}", file=sys.stderr)

    if cpp_process is None or cpp_process.poll() is not None:
        print("C++ process is not running or has exited. Cannot get AI move.", file=sys.stderr)
        raise HTTPException(status_code=503, detail="AI service backend not available or has exited.")

    # --- Xác định các ô bị chặn từ board input ---
    removed_cells_found: List[Tuple[int, int]] = []
    for r_idx, row_content in enumerate(request_data.board):
        for c_idx, cell_val in enumerate(row_content):
            if cell_val == -1:
                removed_cells_found.append((r_idx, c_idx))
    
    r1, c1, r2, c2 = 0,0,0,0 # Giá trị mặc định an toàn
    if len(removed_cells_found) == 1:
        r1, c1 = removed_cells_found[0]
        r2, c2 = r1, c1 # Gửi tọa độ trùng nhau cho C++ Position constructor
        print(f"Found 1 removed cell: ({r1},{c1}). Sending as ({r1},{c1}) & ({r2},{c2}) to C++.", file=sys.stderr)
    elif len(removed_cells_found) >= 2:
        r1, c1 = removed_cells_found[0]
        r2, c2 = removed_cells_found[1]
        if len(removed_cells_found) > 2:
             print(f"Warning: Found {len(removed_cells_found)} removed cells. Using first two: ({r1},{c1}) & ({r2},{c2}).", file=sys.stderr)
        else:
             print(f"Found 2 removed cells: ({r1},{c1}) & ({r2},{c2}).", file=sys.stderr)
    else: # 0 ô bị chặn
        print(f"Found 0 removed cells. Using default ({r1},{c1}) & ({r2},{c2}) for C++.", file=sys.stderr)
    # ------------------------------------------

    try:
        # Giao thức gửi sang C++:
        # 1. Lệnh "GET_MOVE"
        # 2. Tọa độ 2 ô bị chặn: r1 c1 r2 c2
        # 3. ID người chơi sẽ đi: current_player
        # 4. Bàn cờ: 6 dòng, mỗi dòng 7 số (0, 1, hoặc 2. Số -1 từ input sẽ được coi là 0 khi gửi)

        cpp_process.stdin.write("GET_MOVE\n")
        cpp_process.stdin.write(f"{r1} {c1} {r2} {c2}\n")
        cpp_process.stdin.write(f"{request_data.current_player}\n") 
        
        board_to_send_str = ""
        for r_idx, row_content in enumerate(request_data.board):
            processed_row = [str(0) if cell == -1 else str(cell) for cell in row_content]
            board_to_send_str += " ".join(processed_row) + "\n"
        cpp_process.stdin.write(board_to_send_str)
        cpp_process.stdin.flush()
        
        print(f"Sent GET_MOVE to C++ for player {request_data.current_player} with effective removed_cells ({r1},{c1}) & ({r2},{c2})", file=sys.stderr)

        # Đọc phản hồi từ C++ (có thể có timeout nếu muốn)
        response_line = ""
        read_timeout = 10.0 # Timeout 10 giây để C++ trả lời (cho mỗi nước đi)
        read_start_time = time.time()
        
        while time.time() - read_start_time < read_timeout:
            if cpp_process.stdout:
                response_line = cpp_process.stdout.readline().strip()
                if response_line: # Nếu đọc được gì đó
                    break 
            if cpp_process.poll() is not None: # Kiểm tra C++ có bị crash giữa chừng
                print("C++ process exited while Python was waiting for stdout.", file=sys.stderr)
                raise HTTPException(status_code=500, detail="AI backend process crashed during move calculation.")
            time.sleep(0.01) # Chờ một chút rồi thử đọc lại
        
        if not response_line: # Nếu timeout mà không đọc được gì
            print(f"Timeout reading response from C++ after {read_timeout}s.", file=sys.stderr)
            raise HTTPException(status_code=504, detail="AI backend timeout.")

        print(f"Received from C++ stdout: '{response_line}'", file=sys.stderr)

        if response_line.startswith("MOVE "):
            try:
                selected_move = int(response_line.split(" ")[1])
                print(f"AI (Player {request_data.current_player}) chose column: {selected_move}", file=sys.stderr)
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
        stderr_dump = ""
        if cpp_process and cpp_process.stderr and not cpp_process.stderr.closed:
            try:
                # Cố gắng đọc phần còn lại của stderr nếu có lỗi
                stderr_dump = cpp_process.stderr.read() 
            except: pass 
        if stderr_dump: print(f"C++ STDERR during error processing: {stderr_dump}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=f"Internal server error during AI communication: {str(e)}")
    finally:
        end_time_req = time.time()
        print(f"Total request processing time for player {request_data.current_player}: {(end_time_req - request_received_time)*1000:.2f} ms", file=sys.stderr)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000)) 
    print(f"Starting Uvicorn server on http://0.0.0.0:{port}")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True) # Thêm reload=True cho dev