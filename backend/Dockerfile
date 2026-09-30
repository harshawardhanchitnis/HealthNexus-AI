FROM python:3.13-slim
WORKDIR /workspace
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/workspace/backend PORT=8000
COPY backend/requirements.txt backend/requirements.txt
ARG INSTALL_FEDERATION_TRAINING=0
RUN pip install --no-cache-dir -r backend/requirements.txt && if [ "$INSTALL_FEDERATION_TRAINING" = "1" ]; then pip install --no-cache-dir torch==2.8.0+cpu --index-url https://download.pytorch.org/whl/cpu; fi
COPY backend backend
COPY data data
COPY scripts/restore_demo.py scripts/restore_demo.py
COPY deployment-assets/demo-assets.zip /tmp/demo-assets.zip
RUN echo "966f452b95d7bacff92ccfdbb0fce8ba1beb4593ad0bcb8064d6c0d03397f7dd  /tmp/demo-assets.zip" | sha256sum -c - && python scripts/restore_demo.py /tmp/demo-assets.zip && python -c "import zipfile; from pathlib import Path; Path('artifacts/deployment-integrity.json').write_bytes(zipfile.ZipFile('/tmp/demo-assets.zip').read('demo-assets-manifest.json'))" && rm /tmp/demo-assets.zip
RUN useradd --uid 10001 --create-home healthnexus && mkdir -p artifacts/federation && chown -R healthnexus:healthnexus artifacts/federation
USER healthnexus
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:'+__import__('os').environ.get('PORT','8000')+'/health')"
CMD ["python", "backend/start.py"]
