FROM mambaorg/micromamba:1.5.10

ARG DUALMAP_COMMIT=157235ec49e6a1f439babbc571c4c02ad1f06aa9
ARG DEBIAN_FRONTEND=noninteractive

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    build-essential \
    ca-certificates \
    ffmpeg \
    git \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

USER $MAMBA_USER
WORKDIR /workspace

RUN git clone --filter=blob:none https://github.com/Eku127/DualMap.git /workspace/DualMap \
    && cd /workspace/DualMap \
    && git checkout ${DUALMAP_COMMIT} \
    && git submodule set-url 3rdparty/mobileclip https://github.com/apple/ml-mobileclip.git \
    && git submodule sync --recursive \
    && git submodule update --init --recursive

RUN micromamba create -y -f /workspace/DualMap/environment.yml \
    && micromamba clean --all --yes

RUN cd /workspace/DualMap/3rdparty/mobileclip \
    && /opt/conda/envs/dualmap/bin/python -m pip install -e . --no-deps

RUN /opt/conda/envs/dualmap/bin/python - <<'PY'
import importlib

modules = [
    "hydra",
    "omegaconf",
    "torch",
    "cv2",
    "imageio",
    "numpy",
    "open3d",
    "open_clip",
    "ultralytics",
    "rerun",
    "faiss",
    "kornia",
    "natsort",
    "scipy",
    "tyro",
    "supervision",
]
missing = []
for module in modules:
    try:
        importlib.import_module(module)
    except Exception as exc:
        missing.append((module, repr(exc)))
if missing:
    raise RuntimeError(f"DualMap dependency import smoke failed: {missing}")
PY

WORKDIR /workspace/DualMap
CMD ["bash", "-lc", "/opt/conda/envs/dualmap/bin/python -m applications.runner_dataset --help"]
