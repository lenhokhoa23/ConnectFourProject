FROM python:3.12.6


WORKDIR /app


RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*


ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY InteractiveSolver.exe ./
RUN chmod +x ./InteractiveSolver.exe 

COPY . .



EXPOSE $PORT


# Khởi chạy ứng dụng với uvicorn
CMD uvicorn app:app --host 0.0.0.0 --port $PORT
