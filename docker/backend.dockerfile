# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install the project into `/app`
WORKDIR /eeva

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

COPY python /eeva

RUN uv sync --locked --no-install-project --no-dev

RUN uv sync --locked --no-dev

# Place executables in the environment at the front of the path
ENV PATH="/eeva/.venv/bin:$PATH"
ENV DATA_PATH="/data"
ENV PROMPT_DIR="/prompts"
ENV OPENAI_API_KEY=""

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Run the FastAPI application by default
# Uses `fastapi dev` to enable hot-reloading when the `watch` sync occurs
# Uses `--host 0.0.0.0` to allow access from outside the container
CMD ["uv", "run", "python", "-m", "eeva", "--host", "0.0.0.0"]