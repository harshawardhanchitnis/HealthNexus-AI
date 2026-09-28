FROM python:3.13-slim
WORKDIR /workspace
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/workspace/backend PORT=8000
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt && pip install --no-cache-dir torch==2.8.0+cpu --index-url https://download.pytorch.org/whl/cpu
COPY backend backend
COPY data data
COPY artifacts/models artifacts/models
COPY artifacts/planning artifacts/planning
RUN useradd --uid 10001 --create-home healthnexus && mkdir -p artifacts/federation && chown -R healthnexus:healthnexus artifacts/federation
USER healthnexus
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:'+__import__('os').environ.get('PORT','8000')+'/health')"
CMD ["python", "backend/start.py"]
