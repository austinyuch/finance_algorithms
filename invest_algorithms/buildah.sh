#!/bin/bash
set -euo pipefail

# Build a container image using uv on a Python 3.13 base.
base_image=python:3.13-slim

# Create a new container from the base image
container=$(buildah from $base_image)

# Install uv (standalone, no pip needed)
buildah copy --from=ghcr.io/astral-sh/uv:latest $container /uv /usr/local/bin/uv

# Set the working directory for the container
buildah config --workingdir /app $container

# Copy project metadata, lockfile and source
buildah copy $container pyproject.toml uv.lock ./
buildah copy $container invest_algorithms ./invest_algorithms

# Install dependencies from the lockfile (no dev deps)
buildah run $container uv sync --frozen --no-dev

# Bind to all interfaces inside the container
buildah config --env API_HOST=0.0.0.0 $container

# Set the entrypoint (run from the source dir so flat imports resolve)
buildah config --workingdir /app/invest_algorithms $container
buildah config --entrypoint '["uv", "run", "--project", "/app", "python", "main.py"]' $container

# Commit the container to an image
buildah commit --format docker $container invest-algorithms:latest

# Clean up the container
buildah rm $container
