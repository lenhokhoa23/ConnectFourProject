FROM python:3.12.6

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1

COPY Position.hpp Solver.hpp MoveSorter.hpp TranspositionTable.hpp ./
COPY Solver.cpp InteractiveSolver.cpp ./ 

# Biên dịch C++
RUN g++ InteractiveSolver.cpp Solver.cpp -o InteractiveSolver -std=c++17 -m64 -O2 -Wall
RUN ls -l /app  
RUN chmod +x ./InteractiveSolver

# Bây giờ copy các file của ứng dụng Python
# Nếu app.py và requirements.txt cũng nằm trong thư mục gốc dự án của bạn
COPY requirements.txt .
COPY app.py . 
# (Nếu bạn có các thư mục con cho Python, COPY chúng vào)

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# EXPOSE $PORT (Biến PORT thường được inject bởi môi trường deploy như Cloud Run)
# Nếu chạy local, bạn có thể hardcode port ở CMD hoặc truyền vào khi docker run
# Ví dụ: EXPOSE 8000

# Khởi chạy ứng dụng với uvicorn
# Đảm bảo app.py của bạn có C_PROCESS_EXEC = "./interactive_solver"
CMD uvicorn app:app --host 0.0.0.0 --port $PORT
