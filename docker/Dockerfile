## Stage 1: 建構前端
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

## Stage 2: Python 後端
FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .

COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

RUN mkdir -p /app/logs

EXPOSE 5050

CMD ["python", "-m", "tw_stock_hot.main"]
