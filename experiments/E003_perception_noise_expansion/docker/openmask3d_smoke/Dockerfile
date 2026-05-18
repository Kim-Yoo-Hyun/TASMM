# E003-M66 OpenMask3D smoke image.
#
# This image is intentionally pinned close to the official OpenMask3D install
# recipe. Build is expected to be long-running and should be launched only from
# the recorded tmux/background command.

FROM nvidia/cuda:11.3.1-cudnn8-devel-ubuntu20.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH=/opt/conda/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    git \
    libgl1 \
    libglib2.0-0 \
    ninja-build \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL --retry 5 --retry-delay 5 https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -b -p /opt/conda \
    && rm /tmp/miniconda.sh \
    && conda clean -afy

RUN conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main \
    && conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r \
    && conda create -y -n openmask3d python=3.8.5 \
    && conda clean -afy

SHELL ["conda", "run", "-n", "openmask3d", "/bin/bash", "-lc"]

RUN python -m pip install "pip<24.1"

WORKDIR /opt
RUN git clone --depth 1 https://github.com/OpenMask3D/openmask3d.git openmask3d

WORKDIR /opt/openmask3d
RUN bash install_requirements.sh \
    && pip install -e .

ENV OPENMASK3D_REPO=/opt/openmask3d
WORKDIR /workspace
