FROM python:3.12-slim

WORKDIR /app

# 先装依赖（利用镜像层缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# 上传目录（main.py 启动时也会 mkdir，这里提前建好便于挂载卷）
RUN mkdir -p uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
