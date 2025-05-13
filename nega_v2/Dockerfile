FROM python:3.12.6

WORKDIR /app

# Cài đặt trình biên dịch C++ (g++) và các công cụ cần thiết
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1

# Copy các file source C++ và header vào trước
COPY Position.hpp ./
COPY Solver.hpp ./
COPY MoveSorter.hpp ./
COPY TranspositionTable.hpp .
# COPY uint_t.hpp ./ # Nếu có file riêng và cần thiết
COPY Solver.cpp ./
COPY InteractiveSolver.cpp ./ 

# Biên dịch C++ bên trong Docker
# Đặt tên file output là 'interactive_solver' (không có .exe cho Linux)
RUN g++ InteractiveSolver.cpp Solver.cpp -o interactive_solver -std=c++17 -m64 -O2

# Cấp quyền thực thi cho file vừa biên dịch
RUN chmod +x ./interactive_solver 

# Copy các file của ứng dụng Python
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY app.py .
# COPY các file Python khác nếu có

# EXPOSE $PORT (PORT sẽ được truyền vào khi chạy container)

# Khởi chạy ứng dụng với uvicorn
# Sửa C_PROCESS_EXEC trong app.py thành "./interactive_solver"
CMD uvicorn app:app --host 0.0.0.0 --port $PORT