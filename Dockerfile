# syntax=docker/dockerfile:1.7
# ---------------------------------------------------------------------------
# Multi-stage image for headless `automata` CLI.
# ---------------------------------------------------------------------------

FROM python:3.13-slim AS builder
WORKDIR /build
COPY pyproject.toml README.md CHANGELOG.md CLAUDE.md /build/
COPY automata_simulator /build/automata_simulator
RUN pip install --no-cache-dir build && python -m build --wheel --outdir /dist .

FROM python:3.13-slim AS runtime
LABEL org.opencontainers.image.title="automata-simulator" \
      org.opencontainers.image.description="Headless CLI for DFA/NFA/PDA/TM simulation" \
      org.opencontainers.image.source="https://github.com/kolesnyk-maksym/automata-simulator" \
      org.opencontainers.image.licenses="MIT"

RUN apt-get update \
    && apt-get install -y --no-install-recommends graphviz \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

# Default workdir lets the user mount automata files.
WORKDIR /work
ENTRYPOINT ["automata"]
CMD ["--help"]
