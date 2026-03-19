FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 安装RDKit
RUN pip install rdkit

# 复制依赖文件
COPY web/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 设置环境变量
ENV PYTHONPATH=/app
ENV FLASK_APP=web/app.py
ENV FLASK_ENV=production

# 暴露端口
EXPOSE 7890

# 启动服务
CMD ["gunicorn", "--bind", "0.0.0.0:7890", "--workers", "4", "--timeout", "120", "web.app:app"]