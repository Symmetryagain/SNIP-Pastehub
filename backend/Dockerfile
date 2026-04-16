# backend/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 设置时区为东八区 (根据你的需求)
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 创建 data 目录用于挂载 SQLite
RUN mkdir -p /app/data

# 启动 Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]