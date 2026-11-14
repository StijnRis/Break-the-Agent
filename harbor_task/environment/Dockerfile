FROM node:22-bookworm-slim

WORKDIR /app
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Include Python for the drawing tools; Node and OpenCode are baked into the
# image so Harbor can detect the installed agent and skip its per-trial setup.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv "$VIRTUAL_ENV" \
    && pip install --no-cache-dir numpy scipy pillow shapely opencv-python-headless \
       scikit-image rapidocr-onnxruntime "mcp>=1.9,<2"
RUN npm install --global opencode-ai@1.19.5

COPY blueprint_env/__init__.py /app/blueprint_env/__init__.py
COPY blueprint_env/env.py /app/blueprint_env/env.py
COPY blueprint_env/mcp_server.py /app/blueprint_env/mcp_server.py
COPY blueprint_env/render.py /app/blueprint_env/render.py
COPY blueprint_env/score.py /app/blueprint_env/score.py
COPY blueprint_env/cv.py /app/blueprint_env/cv.py
COPY task/drawing.png /app/tasks/site279_bldg514_floor2041/drawing.png
CMD ["bash"]
