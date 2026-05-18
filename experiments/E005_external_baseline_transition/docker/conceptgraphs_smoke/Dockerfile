FROM mambaorg/micromamba:1.5.10

ARG CONCEPTGRAPHS_COMMIT=93277a02bd89171f8121e84203121cf7af9ebb5d
ARG GSA_COMMIT=a4d76a2b55e348943cba4cd57d7553c354296223
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    cmake \
    curl \
    ffmpeg \
    gcc-11 \
    g++-11 \
    git \
    libgl1 \
    libglib2.0-0 \
    libxext6 \
    libxrender1 \
    ninja-build \
    python3-tk \
    wget \
    && rm -rf /var/lib/apt/lists/*

USER $MAMBA_USER
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
    | sh -s -- -y --profile minimal --default-toolchain stable

RUN micromamba create -y -n conceptgraph \
    -c pytorch -c nvidia -c conda-forge \
    python=3.10 \
    pytorch=2.0.1 \
    torchvision=0.15.2 \
    torchaudio=2.0.2 \
    pytorch-cuda=11.8 \
    faiss-cpu=1.7.4 \
    mkl=2021 \
    blas=1.0=mkl \
    cudatoolkit-dev \
    cmake \
    ninja \
    && micromamba clean --all --yes

RUN wget -c -O /tmp/pytorch3d-0.7.4-py310_cu118_pyt201.tar.bz2 \
    https://anaconda.org/pytorch3d/pytorch3d/0.7.4/download/linux-64/pytorch3d-0.7.4-py310_cu118_pyt201.tar.bz2 \
    && tar --exclude='info' -xjf /tmp/pytorch3d-0.7.4-py310_cu118_pyt201.tar.bz2 -C /opt/conda/envs/conceptgraph \
    && rm -f /tmp/pytorch3d-0.7.4-py310_cu118_pyt201.tar.bz2 \
    && /opt/conda/envs/conceptgraph/bin/python -c "import pytorch3d; import pytorch3d.ops; print('pytorch3d_manual_extract_ok')"

ENV AM_I_DOCKER=1 \
    BUILD_WITH_CUDA=1 \
    CUDA_HOME=/opt/conda/envs/conceptgraph \
    FORCE_CUDA=1 \
    GSA_PATH=/workspace/Grounded-Segment-Anything \
    MPLBACKEND=Agg \
    CARGO_HOME=/home/mambauser/.cargo \
    CC=/usr/bin/gcc-11 \
    CXX=/usr/bin/g++-11 \
    RUSTUP_HOME=/home/mambauser/.rustup \
    RUSTFLAGS="-A invalid_reference_casting" \
    TORCH_CUDA_ARCH_LIST="8.0;8.6+PTX" \
    PATH=/home/mambauser/.cargo/bin:/opt/conda/envs/conceptgraph/bin:$PATH \
    PYTHONPATH=/workspace/concept-graphs:/workspace/Grounded-Segment-Anything:/workspace/Grounded-Segment-Anything/Tag2Text:/workspace/Grounded-Segment-Anything/GroundingDINO:/workspace/Grounded-Segment-Anything/segment_anything

RUN /opt/conda/envs/conceptgraph/bin/python -m pip install --upgrade pip==23.3.2 setuptools==69.5.1 wheel
RUN /opt/conda/envs/conceptgraph/bin/python -m pip install --no-cache-dir \
    addict \
    diffusers \
    distinctipy \
    fairscale==0.4.4 \
    gradio \
    h5py \
    huggingface_hub \
    hydra-core \
    imageio \
    imageio-ffmpeg \
    matplotlib \
    natsort \
    nltk \
    numpy==1.26.4 \
    omegaconf \
    onnxruntime \
    open_clip_torch \
    openai \
    open3d==0.18.0 \
    opencv-python==4.8.1.78 \
    opencv-python-headless==4.8.1.78 \
    pandas \
    pillow \
    pycocoevalcap \
    pycocotools \
    requests \
    scikit-learn \
    scipy \
    supervision==0.6.0 \
    termcolor \
    timm==0.4.12 \
    tqdm \
    transformers==4.15.0 \
    tyro \
    ultralytics \
    wandb \
    yapf

USER root
RUN mkdir -p /workspace && chown -R ${MAMBA_USER}:${MAMBA_USER} /workspace
USER $MAMBA_USER

RUN git clone https://github.com/concept-graphs/concept-graphs.git /workspace/concept-graphs \
    && git -C /workspace/concept-graphs checkout "${CONCEPTGRAPHS_COMMIT}" \
    && git clone https://github.com/IDEA-Research/Grounded-Segment-Anything.git /workspace/Grounded-Segment-Anything \
    && git -C /workspace/Grounded-Segment-Anything checkout "${GSA_COMMIT}" \
    && git -C /workspace/Grounded-Segment-Anything submodule update --init --recursive

RUN /opt/conda/envs/conceptgraph/bin/python -m pip install --no-cache-dir git+https://github.com/krrish94/chamferdist.git \
    && /opt/conda/envs/conceptgraph/bin/python -m pip install --no-cache-dir git+https://github.com/gradslam/gradslam.git@conceptfusion \
    && /opt/conda/envs/conceptgraph/bin/python -m pip install --no-deps -e /workspace/concept-graphs \
    && /opt/conda/envs/conceptgraph/bin/python -m pip install --no-deps -e /workspace/Grounded-Segment-Anything/segment_anything \
    && /opt/conda/envs/conceptgraph/bin/python -m pip install --no-deps -e /workspace/Grounded-Segment-Anything/GroundingDINO

# Headless smoke compatibility: ConceptGraphs forces TkAgg, and its pinned
# GSA commit has Tag2Text modules but no top-level `ram` package.
RUN sed -i 's/matplotlib.use("TkAgg")/matplotlib.use("Agg")/' /workspace/concept-graphs/conceptgraph/scripts/generate_gsa_results.py \
    && mkdir -p /workspace/Grounded-Segment-Anything/ram/models \
    && printf 'from . import models\nfrom . import inference_ram\nfrom . import inference_tag2text\n' > /workspace/Grounded-Segment-Anything/ram/__init__.py \
    && printf 'from models.tag2text import ram, tag2text_caption as tag2text\n' > /workspace/Grounded-Segment-Anything/ram/models/__init__.py \
    && printf 'from inference_ram import *\n' > /workspace/Grounded-Segment-Anything/ram/inference_ram.py \
    && printf 'from inference_tag2text import *\n' > /workspace/Grounded-Segment-Anything/ram/inference_tag2text.py

COPY import_smoke.py /opt/research2/import_smoke.py
RUN /opt/conda/envs/conceptgraph/bin/python /opt/research2/import_smoke.py

WORKDIR /workspace/concept-graphs/conceptgraph
CMD ["/opt/conda/envs/conceptgraph/bin/python", "/opt/research2/import_smoke.py"]
