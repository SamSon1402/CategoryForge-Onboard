FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY configs ./configs
COPY dashboard ./dashboard
RUN pip install --no-cache-dir .
EXPOSE 8000
CMD ["uvicorn", "category_forge.service:app", "--host", "0.0.0.0", "--port", "8000"]
