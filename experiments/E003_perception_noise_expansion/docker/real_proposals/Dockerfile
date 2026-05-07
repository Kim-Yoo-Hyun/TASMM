FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
        torch==2.5.1 torchvision==0.20.1 \
    && python -m pip install --no-cache-dir \
        numpy==1.26.4 \
        pillow==10.4.0 \
        safetensors==0.4.5 \
        timm==1.0.19 \
        transformers==4.57.1

RUN mkdir -p /workspace/tools
COPY run_rgbd_ov_proposals.py /workspace/tools/run_rgbd_ov_proposals.py

CMD ["python", "/workspace/tools/run_rgbd_ov_proposals.py", "--help"]
