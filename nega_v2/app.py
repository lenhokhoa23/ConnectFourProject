from fastapi import FastAPI, HTTPException, Body
import random
import uvicorn
import os
import subprocess
from pydantic import BaseModel
from typing import List, Optional, Tuple 
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys 
import time 
import fcntl

C_PROCESS_EXEC = "./InteractiveSolver" 
cpp_process: Optional[subprocess.Popen] = None

# lifespan giữ nguyên như phiên bản trước (đã có sửa lỗi stderr None và non-blocking read)
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
            universal_newlines=True 
        )
        print(f"C++ process started with PID: {cpp_process.pid}")

        if cpp_process.stderr:
            fd = cpp_process.stderr.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        timeout_start = time.time()
        startup_timeout = 20 

        while time.time() - timeout_start < startup_timeout:
            if cpp_process.poll() is not None: 
                print("C++ process exited prematurely during startup.", file=sys.stderr)
                stdout_dump = cpp_process.stdout.read() if cpp_process.stdout else ""
                stderr_dump = cpp_process.stderr.read() if cpp_process.stderr else "" 
                if stdout_dump: print(f"C++ STDOUT DUMP ON FAILURE: {stdout_dump}", file=sys.stderr)
                if stderr_dump: print(f"C++ STDERR DUMP ON FAILURE: {stderr_dump}", file=sys.stderr)
                cpp_process = None 
                break

            line = ""
            if cpp_process.stderr: 
                try:
                    line = cpp_process.stderr.readline().strip()
                except BlockingIOError: 
                    time.sleep(0.1) 
                    continue 
                except Exception as e_read:
                    print(f"Exception reading stderr: {e_read}", file=sys.stderr)
                    time.sleep(0.1)
                    continue
            
            if line: 
                print(f"C++_STDERR: {line}", file=sys.stderr) 
                if "READY" in line:
                    print("C++ process reported READY.")
                    cpp_ready = True
                    break
                if "FATAL_ERROR" in line.upper() or "ERROR:" in line.upper(): 
                    print("C++ process reported an error during startup via stderr.", file=sys.stderr)
                    break 
            else: 
                time.sleep(0.1) 

        if not cpp_ready: # Xử lý nếu không READY sau timeout
            print("C++ process failed to report READY or reported an error within timeout. AI service might be unavailable.", file=sys.stderr)
            if cpp_process and cpp_process.poll() is None: # Nếu vẫn chạy thì kill
                print("C++ process is still running but did not signal READY. Killing.", file=sys.stderr)
                try: cpp_process.kill(); cpp_process.wait(timeout=1) # Thêm wait
                except Exception: pass
            cpp_process = None # Đặt là None nếu không sẵn sàng hoặc đã kill

    except FileNotFoundError:
        print(f"FATAL ERROR: C++ executable not found at {C_PROCESS_EXEC}. Ensure it's built and path is correct in Dockerfile.", file=sys.stderr)
        cpp_process = None
    except Exception as e:
        print(f"An error occurred while starting C++ process: {e}", file=sys.stderr)
        if cpp_process and cpp_process.poll() is None:
            try: cpp_process.kill(); cpp_process.wait(timeout=1)
            except Exception: pass
        cpp_process = None
    
    yield 

    print("App shutdown: Stopping C++ process...")
    if cpp_process and cpp_process.poll() is None:
        try:
            if cpp_process.stdin:
                cpp_process.stdin.write("QUIT\n")
                cpp_process.stdin.flush()
            cpp_process.wait(timeout=5) 
            print("C++ process stopped gracefully.", file=sys.stderr)
        except subprocess.TimeoutExpired:
            print(f"C++ process did not exit after QUIT command and 5s timeout. Killing.", file=sys.stderr)
            try: cpp_process.kill()
            except Exception as e_kill: print(f"Error killing C++ process: {e_kill}", file=sys.stderr)
        except Exception as e: 
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


# SỬA LẠI PYDANTIC MODEL CHO REQUEST ĐỂ KHỚP YÊU CẦU CỦA NỀN TẢNG KIỂM THỬ
class GameStateRequest(BaseModel):
    board: List[List[int]] 
    current_player: int    
    valid_moves: List[int] # Thêm lại trường này theo yêu cầu của API Format
    is_new_game: bool      # Thêm trường này theo yêu cầu của API Format

class AIResponse(BaseModel):
    move: int 

# Giữ nguyên đường dẫn endpoint này nếu nó đã hoạt động trên Render trước đó
# Nếu nền tảng tự động thêm /api/connect4-move, bạn cần kiểm tra lại
@app.post("/api/connect4-move", response_model=AIResponse) # SỬA THÀNH ĐƯỜNG DẪN MÀ NỀN TẢNG GỢI Ý
async def get_ai_move_endpoint(request_data: GameStateRequest = Body(...)):
    request_received_time = time.time()
    print(f"Received request for /api/connect4-move for player {request_data.current_player}", file=sys.stderr)

    print(f"Received request for /api/get_ai_move for player {request_data.current_player}", file=sys.stderr)
    # In ra is_new_game và valid_moves để kiểm tra (tùy chọn)
    print(f"is_new_game: {request_data.is_new_game}", file=sys.stderr)
    print(f"valid_moves from client: {request_data.valid_moves}", file=sys.stderr)


    if cpp_process is None or cpp_process.poll() is not None:
        # ... (xử lý lỗi cpp_process không chạy như cũ) ...
        print("C++ process is not running or has exited. Cannot get AI move.", file=sys.stderr)
        raise HTTPException(status_code=503, detail="AI service backend not available or has exited.")


    removed_cells_found: List[Tuple[int, int]] = []
    for r_idx, row_content in enumerate(request_data.board):
        for c_idx, cell_val in enumerate(row_content):
            if cell_val == -1:
                removed_cells_found.append((r_idx, c_idx))
    
    r1, c1, r2, c2 = 0,0,0,0 
    if len(removed_cells_found) == 1:
        r1, c1 = removed_cells_found[0]
        r2, c2 = r1, c1 
        print(f"Found 1 removed cell: ({r1},{c1}). Sending as ({r1},{c1}) & ({r2},{c2}) to C++.", file=sys.stderr)
    elif len(removed_cells_found) >= 2:
        r1, c1 = removed_cells_found[0]
        r2, c2 = removed_cells_found[1]
        if len(removed_cells_found) > 2:
             print(f"Warning: Found {len(removed_cells_found)} removed cells. Using first two: ({r1},{c1}) & ({r2},{c2}).", file=sys.stderr)
        else:
             print(f"Found 2 removed cells: ({r1},{c1}) & ({r2},{c2}).", file=sys.stderr)
    else: 
        print(f"Found 0 removed cells. Using default ({r1},{c1}) & ({r2},{c2}) for C++.", file=sys.stderr)
    
    try:
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

        response_line = ""
        read_timeout = 10.0 
        read_start_time = time.time()
        
        while time.time() - read_start_time < read_timeout:
            if cpp_process.stdout:
                try: # Thêm try-except khi đọc stdout
                    response_line = cpp_process.stdout.readline().strip()
                    if response_line: 
                        break 
                except BlockingIOError: # Xử lý lỗi nếu stdout đang non-blocking và không có gì
                    pass # Bỏ qua và thử lại
                except Exception as e_read_stdout:
                    print(f"Exception reading stdout: {e_read_stdout}", file=sys.stderr)
                    # Có thể raise lỗi ở đây nếu muốn
                    break # Thoát vòng lặp đọc nếu có lỗi nghiêm trọng
            if cpp_process.poll() is not None: 
                print("C++ process exited while Python was waiting for stdout.", file=sys.stderr)
                raise HTTPException(status_code=500, detail="AI backend process crashed during move calculation.")
            time.sleep(0.01) 
        
        if not response_line: 
            print(f"Timeout reading response from C++ after {read_timeout}s.", file=sys.stderr)
            raise HTTPException(status_code=504, detail="AI backend timeout.")

        print(f"Received from C++ stdout: '{response_line}'", file=sys.stderr)

        if response_line.startswith("MOVE "):
            try:
                selected_move = int(response_line.split(" ")[1])
                # Kiểm tra xem nước đi có nằm trong valid_moves (nếu client gửi) không
                if request_data.valid_moves and selected_move not in request_data.valid_moves:
                    print(f"CRITICAL WARNING: AI move {selected_move} IS NOT in valid_moves {request_data.valid_moves} from client!", file=sys.stderr)
                    # Quyết định: Dùng nước của AI, hay dùng fallback, hay báo lỗi?
                    # Để an toàn, nếu có valid_moves từ client và AI trả về nước không hợp lệ, có thể chọn fallback
                    # raise HTTPException(status_code=500, detail=f"AI returned an invalid move {selected_move} not in {request_data.valid_moves}")
                    # Hoặc, nếu bạn tin C++ Solver của mình hơn:
                    print(f"AI (Player {request_data.current_player}) chose column: {selected_move} (ignoring client valid_moves check for now)", file=sys.stderr)

                else: # Nước đi của AI hợp lệ hoặc client không gửi valid_moves
                    print(f"AI (Player {request_data.current_player}) chose column: {selected_move}", file=sys.stderr)
                
                return AIResponse(move=selected_move)
            # ... (các except và finally như cũ) ...
            except (ValueError, IndexError):
                print(f"Error parsing MOVE from C++: '{response_line}'", file=sys.stderr)
                raise HTTPException(status_code=500, detail="AI returned invalid move format.")
        elif response_line.startswith("ERROR"): # Các nhánh else if/else giữ nguyên
            print(f"C++ process reported an error: {response_line}", file=sys.stderr)
            raise HTTPException(status_code=500, detail=f"AI calculation error: {response_line}")
        else:
            print(f"Unexpected response from C++: '{response_line}'", file=sys.stderr)
            raise HTTPException(status_code=500, detail="AI returned unexpected response.")

    except Exception as e:
        print(f"An unexpected error occurred in get_ai_move_endpoint: {type(e).__name__} - {e}", file=sys.stderr)
        stderr_dump = ""
        if cpp_process and cpp_process.stderr and not cpp_process.stderr.closed:
            try:
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
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)