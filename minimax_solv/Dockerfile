FROM python:3.12.6


WORKDIR /app


# Cài đặt dependencies cơ bản
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*


# Cấu hình môi trường
ENV PYTHONUNBUFFERED=1


# Copy file requirements.txt và cài đặt dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt


# Copy mã nguồn
COPY . .


# Sử dụng biến môi trường PORT (do Render cung cấp)
EXPOSE $PORT


# Khởi chạy ứng dụng với uvicorn
CMD uvicorn app:app --host 0.0.0.0 --port $PORT
