# Stage 1: Build frontend (always runs on the build host — output is static)
FROM --platform=$BUILDPLATFORM node:24-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.14-slim

LABEL org.opencontainers.image.source="https://github.com/uprightbass360/automatic-ripping-machine-ui"
LABEL org.opencontainers.image.license="MIT"
LABEL org.opencontainers.image.description="Replacement dashboard for ARM (SvelteKit + FastAPI)"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY VERSION .
COPY backend/ backend/

# Copy built frontend into place for static serving
COPY --from=frontend-build /app/frontend/build frontend/build

EXPOSE 8888

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8888"]
